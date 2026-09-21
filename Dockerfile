FROM odoo:19.0
USER root
RUN pip3 install --break-system-packages --ignore-installed \
    packaging \
    "fastapi>=0.110.0" \
    python-multipart \
    ujson \
    "a2wsgi>=1.10.6" \
    parse-accept-language \
    pydantic
USER odoo
