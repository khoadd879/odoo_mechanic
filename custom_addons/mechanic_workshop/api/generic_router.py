from datetime import date, datetime
from typing import Annotated, Any, Optional

from odoo.api import Environment
from odoo.addons.fastapi.dependencies import odoo_env

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Path, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

generic_router = APIRouter()


# ---------------------------------------------------------------------------
# Helper Serialization Functions
# ---------------------------------------------------------------------------
def _serialize_value(v: Any) -> Any:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, dict):
        return {k: _serialize_value(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_serialize_value(item) for item in v]
    return v


def _clean_data(data: Any) -> Any:
    if isinstance(data, list):
        return [_clean_data(item) for item in data]
    if isinstance(data, dict):
        return {k: _serialize_value(v) for k, v in data.items()}
    return _serialize_value(data)


async def get_env_with_auth(
    env: Annotated[Environment, Depends(odoo_env)],
    api_key: Annotated[
        Optional[str],
        Header(
            alias="api-key",
            description="Odoo User API Key. If provided, requests execute under that user's security context.",
        ),
    ] = None,
) -> Environment:
    if api_key:
        try:
            uid = env["res.users.apikeys"].sudo()._check_credentials(scope="rpc", key=api_key)
            if uid:
                return env(user=uid)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed with API Key")
    return env


def _get_model(env: Environment, model_name: str):
    if model_name not in env:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' does not exist in Odoo database.",
        )
    return env[model_name]


# ---------------------------------------------------------------------------
# Pydantic Schemas for Explicit Business Resources
# ---------------------------------------------------------------------------
class CustomerCreateSchema(BaseModel):
    name: str = Field(..., description="Full Name of the Customer or Company", examples=["Nguyen Van An"])
    email: Optional[str] = Field(None, description="Email address", examples=["an.nguyen@example.com"])
    phone: Optional[str] = Field(None, description="Phone number", examples=["0912345678"])
    street: Optional[str] = Field(None, description="Street address", examples=["123 Duong 3/2"])
    city: Optional[str] = Field(None, description="City / Province", examples=["TP Ho Chi Minh"])
    vat: Optional[str] = Field(None, description="Tax Identification Number (MST)", examples=["0312345678"])
    is_company: bool = Field(default=False, description="True if customer is a corporate legal entity")


class CustomerUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Full Name of the Customer or Company", examples=["Cong ty TNHH Co Khi Sai Gon"])
    email: Optional[str] = Field(None, description="Email address", examples=["info@saigon-mechanic.vn"])
    phone: Optional[str] = Field(None, description="Phone number", examples=["02838123456"])
    street: Optional[str] = Field(None, description="Street address", examples=["456 Quoc Lo 1A"])
    city: Optional[str] = Field(None, description="City / Province", examples=["Binh Duong"])
    vat: Optional[str] = Field(None, description="Tax Identification Number (MST)", examples=["3701234567"])
    is_company: Optional[bool] = Field(None, description="True if customer is a corporate legal entity")


class ProductCreateSchema(BaseModel):
    name: str = Field(..., description="Product / Part Name", examples=["Van mot chieu Yoshitake DN50"])
    default_code: Optional[str] = Field(None, description="Internal SKU / Reference", examples=["YOSH-CV-DN50"])
    list_price: float = Field(default=0.0, ge=0.0, description="Sale Price (VND)", examples=[1850000.0])
    standard_price: float = Field(default=0.0, ge=0.0, description="Cost Price (VND)", examples=[1200000.0])
    description: Optional[str] = Field(None, description="Technical specifications or description", examples=["Van 1 chieu la lat inox 316 ket noi mat bich JIS 10K"])
    product_brand_id: Optional[int] = Field(None, description="Brand ID in product.brand", examples=[1])


class ProductUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Product / Part Name")
    default_code: Optional[str] = Field(None, description="Internal SKU / Reference")
    list_price: Optional[float] = Field(None, ge=0.0, description="Sale Price (VND)")
    standard_price: Optional[float] = Field(None, ge=0.0, description="Cost Price (VND)")
    description: Optional[str] = Field(None, description="Technical specifications or description")
    product_brand_id: Optional[int] = Field(None, description="Brand ID in product.brand")


class RFQLineItemSchema(BaseModel):
    product_id: int = Field(..., description="Odoo product.product variant ID", examples=[56])
    quantity: float = Field(default=1.0, gt=0, description="Requested quantity", examples=[2.0])
    notes: Optional[str] = Field(None, description="Part requirements or notes", examples=["Requires DN50 flange"])


class RFQCreateSchema(BaseModel):
    contact_name: str = Field(..., description="Customer contact person name", examples=["Tran Minh Tri"])
    contact_email: str = Field(..., description="Customer email", examples=["tri.tran@example.com"])
    contact_phone: Optional[str] = Field(None, description="Customer phone", examples=["0987654321"])
    company_name: Optional[str] = Field(None, description="Company or factory name", examples=["Nha may Bia Sai Gon"])
    project_name: Optional[str] = Field(None, description="Project or equipment identifier", examples=["Bao tri Lo hoi so 2"])
    notes: Optional[str] = Field(None, description="General project requirements", examples=["Bao gia gap trong ngay, can CO/CQ"])
    lines: list[RFQLineItemSchema] = Field(..., description="List of parts requested", min_length=1)


class GenericSearchRequest(BaseModel):
    domain: list[Any] = Field(default=[], description="Odoo domain filter, e.g. [['name', 'ilike', 'valve']]", examples=[[]])
    fields: Optional[list[str]] = Field(default=None, description="Fields to return, e.g. ['id', 'name']", examples=[["id", "name"]])
    limit: int = Field(default=50, ge=1, le=1000, description="Max records to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    order: Optional[str] = Field(default=None, description="Sort order, e.g. 'name asc'")


class GenericValuesRequest(BaseModel):
    values: dict[str, Any] = Field(..., description="Dictionary of model fields and values", examples=[{"name": "New Entry"}])


# ---------------------------------------------------------------------------
# 0. Modern Documentation & Landing Endpoints
# ---------------------------------------------------------------------------
@generic_router.get(
    "/",
    tags=["0. Developer Portal & Documentation"],
    summary="API Gateway Landing & Directory",
    description="Welcome portal for developers. Returns API directory or redirects to modern interactive docs.",
)
def api_gateway_index(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse(url="/api/v1/scalar")
    return {
        "portal": "Mechanic Workshop API & Developer Hub",
        "version": "1.0.0",
        "documentation": {
            "scalar_modern_portal": "/api/v1/scalar",
            "swagger_classic_ui": "/api/v1/docs",
            "openapi_specification": "/api/v1/openapi.json",
        },
        "resources": {
            "customers": "/api/v1/customers",
            "products": "/api/v1/products",
            "rfqs": "/api/v1/rfqs",
            "boilers": "/api/v1/boilers",
            "universal_orm": "/api/v1/orm/{model}",
        },
    }


@generic_router.api_route(
    "/scalar",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    tags=["0. Developer Portal & Documentation"],
    summary="Open Modern 3-Column API Docs (Scalar)",
    description="Loads the modern Stripe-style API documentation portal with interactive code generation for Flutter (Dart), React, Python, and cURL.",
)
def get_scalar_docs():
    html_content = """<!doctype html>
<html lang="vi">
  <head>
    <title>Mechanic Workshop Developer Portal & API</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" type="image/svg+xml" href="https://scalar.com/favicon.svg" />
    <style>
      body { margin: 0; padding: 0; }
      .custom-header {
        background: #18181b;
        color: #f4f4f5;
        padding: 8px 16px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #27272a;
      }
      .custom-header a {
        color: #a855f7;
        text-decoration: none;
        margin-left: 12px;
        font-weight: 500;
      }
      .custom-header a:hover {
        text-decoration: underline;
      }
    </style>
  </head>
  <body>
    <div class="custom-header">
      <div>⚙️ <strong>Mechanic Workshop Developer Hub</strong> | Odoo 19.0 API Portal</div>
      <div>
        <a href="/api/v1/docs">Swagger UI truyền thống</a>
        <a href="/api/v1/openapi.json" target="_blank">OpenAPI JSON</a>
        <a href="/web" target="_blank">Vào Odoo Web</a>
      </div>
    </div>
    <script
      id="api-reference"
      data-url="/api/v1/openapi.json"
      data-configuration='{
        "theme": "purple",
        "layout": "modern",
        "darkMode": true,
        "showSidebar": true,
        "searchHotKey": "k",
        "defaultHttpClient": {
          "targetKey": "dart",
          "clientKey": "http"
        }
      }'></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>"""
    return HTMLResponse(content=html_content)


# ---------------------------------------------------------------------------
# 1. Customers & Contacts Resource
# ---------------------------------------------------------------------------
@generic_router.get(
    "/customers",
    tags=["1. Customers & Contacts (Khách hàng)"],
    summary="Get List of Customers",
    description="Retrieve customers and business partners with filter by search keyword, phone, or email.",
)
def get_customers(
    env: Annotated[Environment, Depends(get_env_with_auth)],
    search: Optional[str] = Query(None, description="Search term for name, email, or phone"),
    limit: int = Query(20, ge=1, le=200, description="Records limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    domain = []
    if search:
        domain = ["|", "|", ("name", "ilike", search), ("email", "ilike", search), ("phone", "ilike", search)]
    fields = ["id", "name", "display_name", "email", "phone", "street", "city", "vat", "is_company"]
    records = env["res.partner"].search_read(domain, fields=fields, offset=offset, limit=limit, order="name asc")
    total = env["res.partner"].search_count(domain)
    return {"total": total, "count": len(records), "customers": _clean_data(records)}


@generic_router.get(
    "/customers/{id}",
    tags=["1. Customers & Contacts (Khách hàng)"],
    summary="Get Customer Details",
    description="Retrieve detailed information for a specific customer by numeric ID.",
)
def get_customer_detail(
    id: int = Path(..., description="Customer ID in res.partner"),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    partner = env["res.partner"].browse(id)
    if not partner.exists():
        raise HTTPException(status_code=404, detail=f"Customer #{id} not found")
    data = partner.read(["id", "name", "email", "phone", "street", "city", "vat", "is_company", "comment"])[0]
    return _clean_data(data)


@generic_router.post(
    "/customers",
    tags=["1. Customers & Contacts (Khách hàng)"],
    summary="Create New Customer",
    description="Create a new customer profile in Odoo.",
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer: CustomerCreateSchema = Body(...),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    try:
        vals = {
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "street": customer.street,
            "city": customer.city,
            "vat": customer.vat,
            "is_company": customer.is_company,
            "customer_rank": 1,
        }
        new_partner = env["res.partner"].create(vals)
        return {
            "success": True,
            "id": new_partner.id,
            "name": new_partner.name,
            "display_name": new_partner.display_name,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@generic_router.put(
    "/customers/{id}",
    tags=["1. Customers & Contacts (Khách hàng)"],
    summary="Update Customer Details",
    description="Update information of an existing customer by ID.",
)
def update_customer(
    id: int = Path(..., description="Customer ID"),
    data: CustomerUpdateSchema = Body(...),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    partner = env["res.partner"].browse(id)
    if not partner.exists():
        raise HTTPException(status_code=404, detail=f"Customer #{id} not found")
    try:
        update_vals = {k: v for k, v in data.model_dump().items() if v is not None}
        if update_vals:
            partner.write(update_vals)
        return {
            "success": True,
            "id": partner.id,
            "name": partner.name,
            "display_name": partner.display_name,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@generic_router.delete(
    "/customers/{id}",
    tags=["1. Customers & Contacts (Khách hàng)"],
    summary="Archive or Delete Customer",
    description="Deactivate (archive) or delete a customer profile by ID.",
)
def delete_customer(
    id: int = Path(..., description="Customer ID"),
    hard_delete: bool = Query(False, description="Set true to permanently delete record, otherwise archive (active=False)"),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    partner = env["res.partner"].browse(id)
    if not partner.exists():
        raise HTTPException(status_code=404, detail=f"Customer #{id} not found")
    try:
        if hard_delete:
            partner.unlink()
            return {"success": True, "id": id, "message": "Customer permanently deleted"}
        partner.write({"active": False})
        return {"success": True, "id": id, "message": "Customer archived successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# 2. Products & Spare Parts Catalog Resource
# ---------------------------------------------------------------------------
@generic_router.get(
    "/products",
    tags=["2. Products & Spares (Phụ tùng & Sản phẩm)"],
    summary="List Spare Parts Catalog",
    description="Search and filter workshop catalog products with SKU, MPN, Brand, and pricing.",
)
def get_products(
    env: Annotated[Environment, Depends(get_env_with_auth)],
    search: Optional[str] = Query(None, description="Search term for product name, SKU, or MPN"),
    brand_id: Optional[int] = Query(None, description="Filter by product.brand ID"),
    limit: int = Query(20, ge=1, le=200, description="Records limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    domain = [("sale_ok", "=", True)]
    if search:
        domain.extend(["|", "|", ("name", "ilike", search), ("default_code", "ilike", search), ("description", "ilike", search)])
    if brand_id:
        domain.append(("product_brand_id", "=", brand_id))
    fields = ["id", "name", "default_code", "list_price", "product_brand_id", "categ_id", "uom_id"]
    records = env["product.template"].search_read(domain, fields=fields, offset=offset, limit=limit, order="name asc")
    total = env["product.template"].search_count(domain)
    return {"total": total, "count": len(records), "products": _clean_data(records)}


@generic_router.get(
    "/products/{id}",
    tags=["2. Products & Spares (Phụ tùng & Sản phẩm)"],
    summary="Get Product Detail",
    description="Retrieve full specifications and details of a spare part by its product.template ID.",
)
def get_product_detail(
    id: int = Path(..., description="Product Template ID"),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    product = env["product.template"].browse(id)
    if not product.exists():
        raise HTTPException(status_code=404, detail=f"Product #{id} not found")
    data = product.read([
        "id", "name", "default_code", "list_price", "product_brand_id",
        "categ_id", "description", "uom_id", "public_categ_ids",
    ])[0]
    return _clean_data(data)


@generic_router.post(
    "/products",
    tags=["2. Products & Spares (Phụ tùng & Sản phẩm)"],
    summary="Create New Product / Spare Part",
    description="Create a new catalog product item in Odoo.",
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductCreateSchema = Body(...),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    try:
        vals = {
            "name": product.name,
            "default_code": product.default_code,
            "list_price": product.list_price,
            "standard_price": product.standard_price,
            "description": product.description,
            "product_brand_id": product.product_brand_id,
            "sale_ok": True,
            "purchase_ok": True,
        }
        new_prod = env["product.template"].create(vals)
        return {
            "success": True,
            "id": new_prod.id,
            "name": new_prod.name,
            "default_code": new_prod.default_code,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@generic_router.put(
    "/products/{id}",
    tags=["2. Products & Spares (Phụ tùng & Sản phẩm)"],
    summary="Update Product / Spare Part",
    description="Update product details by ID.",
)
def update_product(
    id: int = Path(..., description="Product Template ID"),
    data: ProductUpdateSchema = Body(...),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    prod = env["product.template"].browse(id)
    if not prod.exists():
        raise HTTPException(status_code=404, detail=f"Product #{id} not found")
    try:
        update_vals = {k: v for k, v in data.model_dump().items() if v is not None}
        if update_vals:
            prod.write(update_vals)
        return {
            "success": True,
            "id": prod.id,
            "name": prod.name,
            "default_code": prod.default_code,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# 3. RFQs & Quotations Resource
# ---------------------------------------------------------------------------
@generic_router.get(
    "/rfqs",
    tags=["3. RFQs & Quotes (Yêu cầu báo giá)"],
    summary="List Workshop RFQs",
    description="Retrieve submitted requests for quotations (RFQs) with status and contact details.",
)
def get_rfqs(
    env: Annotated[Environment, Depends(get_env_with_auth)],
    state: Optional[str] = Query(None, description="Filter by state: submitted, quoted"),
    limit: int = Query(20, ge=1, le=200, description="Records limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    domain = []
    if state:
        domain.append(("state", "=", state))
    fields = ["id", "name", "contact_name", "company_name", "email", "phone", "project_name", "state", "create_date"]
    records = env["sre.rfq"].search_read(domain, fields=fields, offset=offset, limit=limit, order="id desc")
    total = env["sre.rfq"].search_count(domain)
    return {"total": total, "count": len(records), "rfqs": _clean_data(records)}


@generic_router.get(
    "/rfqs/{id}",
    tags=["3. RFQs & Quotes (Yêu cầu báo giá)"],
    summary="Get RFQ Detail by ID",
    description="Retrieve complete RFQ details including contact details and all requested line items.",
)
def get_rfq_detail(
    id: int = Path(..., description="RFQ ID"),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    rfq = env["sre.rfq"].browse(id)
    if not rfq.exists():
        raise HTTPException(status_code=404, detail=f"RFQ #{id} not found")
    data = rfq.read([
        "id", "name", "contact_name", "company_name", "email", "phone",
        "project_name", "project_location", "required_delivery_date",
        "notes", "equipment_make_model", "operating_medium",
        "operating_pressure", "operating_temperature", "state",
        "create_date", "lead_id", "order_id"
    ])[0]
    lines = []
    for line in rfq.line_ids:
        lines.append({
            "id": line.id,
            "product_id": line.product_id.id,
            "product_name": line.product_id.display_name,
            "default_code": line.product_id.default_code,
            "quantity": line.quantity,
            "uom": line.uom_id.name if line.uom_id else None,
        })
    data["lines"] = lines
    return _clean_data(data)


@generic_router.post(
    "/rfqs",
    tags=["3. RFQs & Quotes (Yêu cầu báo giá)"],
    summary="Submit New RFQ",
    description="Submit a new request for quotation from customer with contact information and line items.",
    status_code=status.HTTP_201_CREATED,
)
def submit_rfq(
    rfq: RFQCreateSchema = Body(...),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    try:
        lines_data = []
        extra_notes = []
        for idx, line in enumerate(rfq.lines, start=1):
            product = env["product.product"].browse(line.product_id)
            if not product.exists():
                raise HTTPException(status_code=400, detail=f"Product variant ID {line.product_id} does not exist")
            lines_data.append((0, 0, {
                "product_id": line.product_id,
                "quantity": line.quantity,
            }))
            if line.notes:
                extra_notes.append(f"- Muc {idx} ({product.display_name}): {line.notes}")

        combined_notes = rfq.notes or ""
        if extra_notes:
            note_str = "\n".join(extra_notes)
            combined_notes = f"{combined_notes}\n\nGhi chu phu tung:\n{note_str}".strip()

        rfq_record = env["sre.rfq"].create({
            "contact_name": rfq.contact_name,
            "company_name": rfq.company_name or rfq.contact_name,
            "email": rfq.contact_email,
            "phone": rfq.contact_phone or "",
            "project_name": rfq.project_name or "",
            "notes": combined_notes,
            "line_ids": lines_data,
        })
        return {
            "success": True,
            "id": rfq_record.id,
            "rfq_code": rfq_record.name,
            "line_count": len(lines_data),
            "state": rfq_record.state,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# 4. Boilers & Equipment Assets Resource
# ---------------------------------------------------------------------------
@generic_router.get(
    "/boilers",
    tags=["4. Boilers & Assets (Thiết bị & Nồi hơi)"],
    summary="List Boiler Models & Specifications",
    description="Retrieve registered boiler models, design pressure, capacity, and manufacturer.",
)
def get_boilers(
    env: Annotated[Environment, Depends(get_env_with_auth)],
    search: Optional[str] = Query(None, description="Search term for model name"),
    limit: int = Query(20, ge=1, le=200, description="Records limit"),
):
    domain = []
    if search:
        domain = [("name", "ilike", search)]
    fields = ["id", "name", "slug", "manufacturer_id", "boiler_type_id", "steam_capacity_kg_h", "design_pressure_bar", "description"]
    records = env["sre.boiler.model"].search_read(domain, fields=fields, limit=limit, order="name asc")
    return {"count": len(records), "boilers": _clean_data(records)}


@generic_router.get(
    "/boilers/manufacturers",
    tags=["4. Boilers & Assets (Thiết bị & Nồi hơi)"],
    summary="List Boiler Manufacturers",
    description="Retrieve boiler makers / manufacturers (Miura, Fulton, Cleaver-Brooks, etc.).",
)
def get_boiler_manufacturers(
    env: Annotated[Environment, Depends(get_env_with_auth)],
    limit: int = Query(50, ge=1, le=200, description="Records limit"),
):
    fields = ["id", "name", "slug", "country_name", "description", "model_count", "part_count"]
    records = env["sre.boiler.manufacturer"].search_read([], fields=fields, limit=limit, order="sequence, name asc")
    return {"count": len(records), "manufacturers": _clean_data(records)}


@generic_router.get(
    "/boilers/{id}",
    tags=["4. Boilers & Assets (Thiết bị & Nồi hơi)"],
    summary="Get Boiler Model Details with Mapped Parts",
    description="Retrieve specific boiler model information along with its compatible replacement parts.",
)
def get_boiler_detail(
    id: int = Path(..., description="Boiler Model ID"),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    model = env["sre.boiler.model"].browse(id)
    if not model.exists():
        raise HTTPException(status_code=404, detail=f"Boiler model #{id} not found")
    data = model.read([
        "id", "name", "slug", "manufacturer_id", "boiler_type_id",
        "steam_capacity_kg_h", "design_pressure_bar", "description"
    ])[0]
    parts = []
    for mapping in model.mapping_ids:
        prod = mapping.product_tmpl_id
        parts.append({
            "mapping_id": mapping.id,
            "product_template_id": prod.id,
            "name": prod.name,
            "default_code": prod.default_code,
            "subsystem": mapping.subsystem_id.name if mapping.subsystem_id else None,
            "position_ref": mapping.position_ref,
            "is_critical_spare": mapping.is_critical_spare,
            "notes": mapping.notes,
        })
    data["compatible_parts"] = parts
    return _clean_data(data)


# ---------------------------------------------------------------------------
# 5. Universal Dynamic ORM Explorer (Any Odoo Table)
# ---------------------------------------------------------------------------
@generic_router.get(
    "/models",
    tags=["5. Universal Dynamic ORM (Mọi bảng Odoo)"],
    summary="List All Odoo Database Models",
    description="List all available tables/models in Odoo database with their descriptions and technical names.",
)
def list_all_models(
    env: Annotated[Environment, Depends(get_env_with_auth)],
    search: Optional[str] = Query(None, description="Filter model name, e.g. 'sale' or 'partner'"),
    limit: int = Query(100, ge=1, le=1000, description="Max models to return"),
):
    domain = []
    if search:
        domain = ["|", ("model", "ilike", search), ("name", "ilike", search)]
    records = env["ir.model"].search_read(domain, fields=["model", "name", "state", "transient"], limit=limit, order="model asc")
    return {"count": len(records), "models": records}


@generic_router.get(
    "/orm/{model}/fields",
    tags=["5. Universal Dynamic ORM (Mọi bảng Odoo)"],
    summary="Inspect Schema / Fields of Any Model",
    description="Get dictionary of all fields, types (char, integer, many2one, etc.), and properties for any model.",
)
def get_any_model_fields(
    model: str = Path(..., description="Odoo model technical name, e.g. 'res.partner', 'sale.order'"),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    Model = _get_model(env, model)
    try:
        fields_info = Model.fields_get(attributes=["string", "type", "required", "readonly", "relation", "help", "selection"])
        return {"model": model, "fields": _clean_data(fields_info)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@generic_router.post(
    "/orm/{model}/search",
    tags=["5. Universal Dynamic ORM (Mọi bảng Odoo)"],
    summary="Search & Read Any Model",
    description="Dynamic search_read on any model using Odoo domain filters and pagination.",
)
def search_any_model(
    model: str = Path(..., description="Odoo model technical name, e.g. 'res.partner', 'account.move'"),
    req: GenericSearchRequest = Body(...),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    Model = _get_model(env, model)
    try:
        records = Model.search_read(domain=req.domain, fields=req.fields, offset=req.offset, limit=req.limit, order=req.order)
        total = Model.search_count(req.domain)
        return {"model": model, "total": total, "count": len(records), "records": _clean_data(records)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@generic_router.get(
    "/orm/{model}/{id}",
    tags=["5. Universal Dynamic ORM (Mọi bảng Odoo)"],
    summary="Read Any Record by ID",
    description="Fetch single record data from any model by ID.",
)
def read_any_record(
    model: str = Path(..., description="Odoo model technical name"),
    id: int = Path(..., description="Record numeric ID"),
    fields: Optional[str] = Query(None, description="Comma-separated fields to return"),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    Model = _get_model(env, model)
    record = Model.browse(id)
    if not record.exists():
        raise HTTPException(status_code=404, detail=f"Record #{id} not found in model '{model}'")
    field_list = [f.strip() for f in fields.split(",") if f.strip()] if fields else None
    data = record.read(field_list)
    return _clean_data(data[0] if data else {})


@generic_router.post(
    "/orm/{model}",
    tags=["5. Universal Dynamic ORM (Mọi bảng Odoo)"],
    summary="Create Record in Any Model",
    description="Create a new record in any model.",
    status_code=status.HTTP_201_CREATED,
)
def create_any_record(
    model: str = Path(..., description="Odoo model technical name"),
    req: GenericValuesRequest = Body(...),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    Model = _get_model(env, model)
    try:
        new_rec = Model.create(req.values)
        return {"success": True, "id": new_rec.id, "display_name": new_rec.display_name, "model": model}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@generic_router.put(
    "/orm/{model}/{id}",
    tags=["5. Universal Dynamic ORM (Mọi bảng Odoo)"],
    summary="Update Record in Any Model",
    description="Update an existing record in any model by ID.",
)
def update_any_record(
    model: str = Path(..., description="Odoo model technical name"),
    id: int = Path(..., description="Record ID"),
    req: GenericValuesRequest = Body(...),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    Model = _get_model(env, model)
    record = Model.browse(id)
    if not record.exists():
        raise HTTPException(status_code=404, detail=f"Record #{id} not found in model '{model}'")
    try:
        record.write(req.values)
        return {"success": True, "id": record.id, "display_name": record.display_name, "model": model}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@generic_router.delete(
    "/orm/{model}/{id}",
    tags=["5. Universal Dynamic ORM (Mọi bảng Odoo)"],
    summary="Delete Record in Any Model",
    description="Delete a record from any model by ID.",
)
def delete_any_record(
    model: str = Path(..., description="Odoo model technical name"),
    id: int = Path(..., description="Record ID"),
    env: Annotated[Environment, Depends(get_env_with_auth)] = None,
):
    Model = _get_model(env, model)
    record = Model.browse(id)
    if not record.exists():
        raise HTTPException(status_code=404, detail=f"Record #{id} not found in model '{model}'")
    try:
        record.unlink()
        return {"success": True, "id": id, "model": model, "message": "Record deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
