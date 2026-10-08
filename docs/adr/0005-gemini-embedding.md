# ADR-0005: Gemini Embeddings và version hóa collection

- **Trạng thái**: Accepted
- **Ngày quyết định**: 2026-10-04
- **Thay thế một phần**: [ADR-0001](0001-embedding-model-bge-m3.md)

## Bối cảnh

Render Free không phù hợp để tải và chạy BGE-M3 local ổn định. Pseudo-vector fallback trong pipeline cũ có thể tạo dữ liệu Qdrant không tương thích ngữ nghĩa mà vẫn có vẻ ingest thành công. Embedding khi ingest và khi truy vấn phải dùng cùng model, task type phù hợp và số chiều.

## Quyết định

- Dùng Google GenAI `gemini-embedding-001`, `output_dimensionality=768`, với `RETRIEVAL_DOCUMENT` lúc ingest và `RETRIEVAL_QUERY` lúc truy vấn.
- Dùng cùng Google API key cấu hình trong `OPENAI_API_KEY`; nếu key thiếu, phản hồi sai số chiều, hoặc Qdrant không sẵn sàng, pipeline phải báo lỗi thay vì sinh vector thay thế hoặc báo thành công.
- Ưu tiên cấu hình riêng `EMBEDDING_API_KEY`; chỉ dùng `OPENAI_API_KEY` dự phòng khi `OPENAI_BASE_URL` trỏ tới Google Generative Language API.
- Không đổi collection 1024 chiều đang có tại chỗ. Tạo collection mới có tên/version riêng, ingest dữ liệu đã xác minh, kiểm tra dimension/count/retrieval trước khi cấu hình production trỏ sang collection đó. Giữ collection cũ để rollback.
- Chỉ gửi văn bản corpus công khai và query người dùng tới Google để tạo embedding. Đây là đánh đổi về quyền riêng tư và phụ thuộc vào dịch vụ/quota bên thứ ba; hệ thống chưa có chế độ opt-out hoặc embedding local trong triển khai này.

## Hệ quả và nghiệm thu

- Re-embed bắt buộc để chuyển dữ liệu cũ; vector 1024 chiều không thể dùng với model 768 chiều.
- Embedding dựa vào quota, mạng và chính sách Google; cần theo dõi quota/chi phí trước khi ingest corpus lớn hoặc tăng lưu lượng.
- Không chuyển production collection cho đến khi vectors thật được tạo và kiểm tra trên collection staging. Unit tests chứng minh cấu hình, normalization, validation và lỗi thiếu key; chúng không chứng minh chất lượng ngữ nghĩa hoặc quota của dịch vụ.
