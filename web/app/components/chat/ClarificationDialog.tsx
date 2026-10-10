"use client";

import { cn } from "@/lib/utils";

interface ClarificationDialogProps {
  question: string;
  onContinue: (formData: FormData) => void;
  onCancel?: () => void;
}

export function ClarificationDialog({
  question,
  onContinue,
  onCancel,
}: ClarificationDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="fixed inset-0 bg-black/50" onClick={onCancel} />
      <div className="relative w-full max-w-md bg-card rounded-xl shadow-xl p-6 animate-slide-up">
        <div className="flex items-center gap-3 mb-4">
          <div className="text-3xl">🤔</div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">
              Cần thêm thông tin
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              {question}
            </p>
          </div>
        </div>

        <form onSubmit={onContinue} className="clarification-form space-y-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-primary mb-1">
              1. Loại đất <span className="text-red-500">*</span>
            </label>
            <select name="land_type" required className="w-full">
              <option value="">Chọn loại đất</option>
              <option value="đất ở">Đất ở</option>
              <option value="đất nông nghiệp">Đất nông nghiệp</option>
              <option value="đất thương mại dịch vụ">Đất thương mại dịch vụ</option>
              <option value="khác">Loại khác</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-primary mb-1">
              2. Quận/Huyện tại Hà Nội <span className="text-red-500">*</span>
            </label>
            <select name="district" required className="w-full">
              <option value="">Chọn quận/huyện</option>
              <option value="Ba Đình">Ba Đình</option>
              <option value="Hoàn Kiếm">Hoàn Kiếm</option>
              <option value="Tây Hồ">Tây Hồ</option>
              <option value="Long Biên">Long Biên</option>
              <option value="Cầu Giấy">Cầu Giấy</option>
              <option value="Đống Đa">Đống Đa</option>
              <option value="Hai Bà Trưng">Hai Bà Trưng</option>
              <option value="Hoàng Mai">Hoàng Mai</option>
              <option value="Thanh Xuân">Thanh Xuân</option>
              <option value="Nam Từ Liêm">Nam Từ Liêm</option>
              <option value="Bắc Từ Liêm">Bắc Từ Liêm</option>
              <option value="Hà Đông">Hà Đông</option>
              <option value="Sơn Tây">Sơn Tây</option>
              <option value="Ba Vì">Ba Vì</option>
              <option value="Chương Mỹ">Chương Mỹ</option>
              <option value="Đan Phượng">Đan Phượng</option>
              <option value="Đông Anh">Đông Anh</option>
              <option value="Gia Lâm">Gia Lâm</option>
              <option value="Hoài Đức">Hoài Đức</option>
              <option value="Mê Linh">Mê Linh</option>
              <option value="Mỹ Đức">Mỹ Đức</option>
              <option value="Phú Xuyên">Phú Xuyên</option>
              <option value="Phúc Thọ">Phúc Thọ</option>
              <option value="Quốc Oai">Quốc Oai</option>
              <option value="Sóc Sơn">Sóc Sơn</option>
              <option value="Thạch Thất">Thạch Thất</option>
              <option value="Thanh Oai">Thanh Oai</option>
              <option value="Thanh Trì">Thanh Trì</option>
              <option value="Thường Tín">Thường Tín</option>
              <option value="Ứng Hòa">Ứng Hòa</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-primary mb-1">
              3. Diện tích đất (m² - tùy chọn)
            </label>
            <input
              type="number"
              name="area"
              placeholder="Ví dụ: 120"
              min="0"
              className="w-full"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 btn-secondary"
            >
              Hủy
            </button>
            <button type="submit" className="btn-primary flex-1">
              Tiếp tục →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export { ClarificationDialog };