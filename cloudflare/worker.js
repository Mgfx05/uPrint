const MAX_PDF_BYTES = 10 * 1024 * 1024;
const PDF_TTL_SECONDS = 24 * 60 * 60;

function apiJson(request, data, status = 200) {
  const origin = request.headers.get("Origin") || "*";
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": origin,
      "access-control-allow-methods": "GET, POST, OPTIONS",
      "access-control-allow-headers": "Content-Type",
      "vary": "Origin",
    },
  });
}

function countPdfPages(bytes) {
  // Basic page-object counting. This works for many standard PDFs but is not
  // a full PDF parser; PDFs using compressed object streams need a parser.
  const text = new TextDecoder("latin1").decode(bytes);
  const matches = text.match(/\/Type\s*\/Page\b/g);
  return matches ? matches.length : 0;
}

function priceFor(pages, copies, printType, paperSize) {
  const rate = (printType === "color" ? 10 : 2) * (paperSize === "a3" ? 2 : 1);
  return { price_per_page: rate, total: pages * copies * rate };
}

async function handleApi(request, env) {
  const url = new URL(request.url);
  const path = url.pathname;

  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "access-control-allow-origin": request.headers.get("Origin") || "*",
        "access-control-allow-methods": "GET, POST, OPTIONS",
        "access-control-allow-headers": "Content-Type",
      },
    });
  }

  if (!env.DB || !env.PDF_STORAGE) {
    return apiJson(request, { detail: "Worker bindings DB and PDF_STORAGE are required." }, 500);
  }

  if (path === "/health" && request.method === "GET") {
    return apiJson(request, { status: "ok", application: "uPrint Cloud API" });
  }

  if (path === "/upload-pdf" && request.method === "POST") {
    try {
      const form = await request.formData();
      const file = form.get("file");
      if (!(file instanceof File)) return apiJson(request, { detail: "PDF file field is required." }, 400);
      if (file.size === 0) return apiJson(request, { detail: "The selected file is empty." }, 400);
      if (file.size > MAX_PDF_BYTES) return apiJson(request, { detail: "File too large. Maximum size is 10 MB." }, 413);
      if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
        return apiJson(request, { detail: "Only PDF files are allowed." }, 400);
      }

      const bytes = await file.arrayBuffer();
      if (new TextDecoder().decode(bytes.slice(0, 5)) !== "%PDF-") {
        return apiJson(request, { detail: "The uploaded file is not a valid PDF." }, 400);
      }
      const pages = countPdfPages(bytes);
      if (pages < 1) {
        return apiJson(request, { detail: "We couldn't count pages in this PDF. Please try exporting it again as a standard PDF." }, 400);
      }

      const fileId = crypto.randomUUID();
      const objectKey = `pdf/${fileId}`;
      await env.PDF_STORAGE.put(objectKey, bytes, {
        expirationTtl: PDF_TTL_SECONDS,
        metadata: { original_filename: file.name.slice(0, 255), content_type: "application/pdf" },
      });

      try {
        await env.DB.prepare(
          "INSERT INTO files (id, original_filename, object_key, file_size, page_count, content_type, uploaded_at, delete_after) VALUES (?, ?, ?, ?, ?, 'application/pdf', datetime('now'), datetime('now', '+24 hours'))"
        ).bind(fileId, file.name.slice(0, 255), objectKey, file.size, pages).run();
      } catch (error) {
        await env.PDF_STORAGE.delete(objectKey);
        throw error;
      }

      return apiJson(request, {
        message: "PDF uploaded successfully",
        file_id: fileId,
        filename: file.name,
        pages,
        file_size_bytes: file.size,
      }, 201);
    } catch (error) {
      console.error("PDF upload failed:", error);
      return apiJson(request, { detail: "PDF upload failed. Please try again." }, 500);
    }
  }

  // Raspberry Pi-only PDF download endpoint. Configure PI_DEVICE_TOKEN as a Worker secret.
  const downloadMatch = path.match(/^\\/download-pdf\\/([0-9a-f-]{36})$/i);
  if (downloadMatch && request.method === "GET") {
    const expectedToken = env.PI_DEVICE_TOKEN;
    const authorization = request.headers.get("Authorization") || "";
    if (!expectedToken) {
      return apiJson(request, { detail: "Print worker authentication is not configured." }, 503);
    }
    if (authorization !== `Bearer ${expectedToken}`) {
      return apiJson(request, { detail: "Unauthorized print worker." }, 401);
    }

    const file = await env.DB.prepare(
      "SELECT original_filename, object_key FROM files WHERE id = ? AND deleted_at IS NULL AND (delete_after IS NULL OR delete_after > datetime('now'))"
    ).bind(downloadMatch[1]).first();
    if (!file) return apiJson(request, { detail: "PDF not found or expired." }, 404);

    const storedObject = await env.PDF_STORAGE.get(file.object_key);
    if (!storedObject) return apiJson(request, { detail: "PDF is no longer available in temporary storage." }, 404);

    const safeFilename = (file.original_filename || "document.pdf").replace(/[\\r\\n"]/g, "_");
    return new Response(storedObject.body, {
      status: 200,
      headers: {
        "content-type": "application/pdf",
        "content-disposition": `attachment; filename="${safeFilename}"; filename*=UTF-8''${encodeURIComponent(safeFilename)}`,
        "content-length": String(storedObject.size),
        "cache-control": "private, no-store",
        "x-content-type-options": "nosniff",
      },
    });
  }

  if (path === "/calculate-pdf-price" && request.method === "GET") {
    const fileId = url.searchParams.get("file_id");
    const copies = Number(url.searchParams.get("copies") || 1);
    const printType = url.searchParams.get("print_type") || "bw";
    const paperSize = url.searchParams.get("paper_size") || "a4";
    if (!fileId) return apiJson(request, { detail: "file_id is required." }, 400);
    if (!Number.isInteger(copies) || copies < 1 || copies > 50) return apiJson(request, { detail: "Copies must be between 1 and 50." }, 400);
    if (!["bw", "color"].includes(printType) || !["a4", "a3"].includes(paperSize)) return apiJson(request, { detail: "Invalid print options." }, 400);

    const file = await env.DB.prepare(
      "SELECT id, original_filename, page_count FROM files WHERE id = ? AND deleted_at IS NULL AND (delete_after IS NULL OR delete_after > datetime('now'))"
    ).bind(fileId).first();
    if (!file) return apiJson(request, { detail: "PDF not found or expired. Please upload it again." }, 404);

    const price = priceFor(file.page_count, copies, printType, paperSize);
    return apiJson(request, {
      file_id: file.id,
      filename: file.original_filename,
      pages: file.page_count,
      copies,
      print_type: printType,
      paper_size: paperSize,
      price_per_page: price.price_per_page,
      total_price: price.total,
    });
  }

  if (path === "/create-order" && request.method === "POST") {
    const fileId = url.searchParams.get("file_id");
    const copies = Number(url.searchParams.get("copies") || 1);
    const printType = url.searchParams.get("print_type") || "bw";
    const paperSize = url.searchParams.get("paper_size") || "a4";
    const sides = url.searchParams.get("sides") || "single";
    const orientation = url.searchParams.get("orientation") || "portrait";

    if (!fileId) return apiJson(request, { detail: "file_id is required." }, 400);
    if (!Number.isInteger(copies) || copies < 1 || copies > 50) return apiJson(request, { detail: "Copies must be between 1 and 50." }, 400);
    if (!["bw", "color"].includes(printType) || !["a4", "a3"].includes(paperSize) ||
        !["single", "double"].includes(sides) || !["portrait", "landscape"].includes(orientation)) {
      return apiJson(request, { detail: "Invalid print options." }, 400);
    }

    const file = await env.DB.prepare(
      "SELECT id, object_key, page_count FROM files WHERE id = ? AND deleted_at IS NULL AND (delete_after IS NULL OR delete_after > datetime('now'))"
    ).bind(fileId).first();
    if (!file) return apiJson(request, { detail: "PDF not found or expired. Please upload it again." }, 404);

    const storedObject = await env.PDF_STORAGE.get(file.object_key);
    if (!storedObject) return apiJson(request, { detail: "The PDF has expired from temporary storage. Please upload it again." }, 404);

    const price = priceFor(file.page_count, copies, printType, paperSize);
    const orderId = "UP-" + crypto.randomUUID().slice(0, 8).toUpperCase();
    const jobId = crypto.randomUUID();

    try {
      await env.DB.batch([
        env.DB.prepare(
          "INSERT INTO orders (id, customer_name, customer_phone, file_id, copies, print_type, paper_size, sides, orientation, amount, payment_status, print_status, created_at, updated_at) VALUES (?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?, 'pending', 'queued', datetime('now'), datetime('now'))"
        ).bind(orderId, fileId, copies, printType, paperSize.toUpperCase(), sides, orientation, price.total),
        env.DB.prepare(
          "INSERT INTO print_jobs (id, order_id, file_id, device_id, status, attempts, created_at) VALUES (?, ?, ?, NULL, 'queued', 0, datetime('now'))"
        ).bind(jobId, orderId, fileId),
      ]);
    } catch (error) {
      console.error("Order creation failed:", error);
      return apiJson(request, { detail: "Could not create the order. Please try again." }, 500);
    }

    return apiJson(request, {
      message: "Order created successfully",
      order_id: orderId,
      file_id: fileId,
      pages: file.page_count,
      copies,
      print_type: printType,
      paper_size: paperSize,
      sides,
      orientation,
      amount: price.total,
      payment_status: "pending",
      print_status: "queued",
    }, 201);
  }

  const orderMatch = path.match(/^\/order\/([A-Za-z0-9-]+)$/);
  if (orderMatch && request.method === "GET") {
    const order = await env.DB.prepare(
      "SELECT id AS order_id, file_id, (SELECT page_count FROM files WHERE files.id = orders.file_id) AS pages, copies, print_type, LOWER(paper_size) AS paper_size, sides, orientation, amount, payment_status, print_status FROM orders WHERE id = ?"
    ).bind(orderMatch[1]).first();
    if (!order) return apiJson(request, { detail: "Order not found." }, 404);
    return apiJson(request, { message: "Order found", ...order });
  }

  return apiJson(request, { detail: "API route not found." }, 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      url.pathname = url.pathname.slice(4);
      return handleApi(new Request(url, request), env);
    }
    if (["/health", "/upload-pdf", "/calculate-pdf-price", "/create-order"].includes(url.pathname) ||
        url.pathname.startsWith("/order/") ||
        url.pathname.startsWith("/download-pdf/")) {
      return handleApi(request, env);
    }
    return new Response("uPrint API is running.", { status: 200 });
  },
};
