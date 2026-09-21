from typing import Any
from odoo import fields, models
from fastapi import APIRouter
from ..api.generic_router import generic_router


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("universal_orm", "Universal Odoo ORM API")],
        ondelete={"universal_orm": "cascade"},
    )

    def _get_fastapi_routers(self) -> list[APIRouter]:
        if self.app == "universal_orm":
            return [generic_router]
        return super()._get_fastapi_routers()

    def _prepare_fastapi_app_params(self) -> dict[str, Any]:
        params = super()._prepare_fastapi_app_params()
        if self.app == "universal_orm":
            params["title"] = "Mechanic Workshop Developer Portal & API"
            params["description"] = (
                "### 🚀 Giao diện tài liệu hiện đại (Modern Developer Portal)\n\n"
                "👉 **[BẤM VÀO ĐÂY ĐỂ MỞ TÀI LIỆU HIỆN ĐẠI (SCALAR DOCS)](/api/v1/scalar)** "
                "— bố cục 3 cột chuẩn Stripe/Linear, tự động tạo sẵn code mẫu cho **Flutter (Dart), React (JavaScript), Python và cURL**!\n\n"
                "---\n\n"
                "Tài liệu bao gồm các nhóm nghiệp vụ chính của Xưởng cơ khí (Khách hàng, Phụ tùng, Báo giá, Nồi hơi) "
                "và công cụ Dynamic ORM cho 100% các bảng trong Odoo."
            )
            params["version"] = "1.0.0"
        return params
