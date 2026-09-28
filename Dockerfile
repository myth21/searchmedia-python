FROM python:3.12-slim

WORKDIR /var/www

# Without this, print() output sits in a buffer instead of reaching docker logs.
ENV PYTHONUNBUFFERED=1

COPY requirements-searchmedia.txt .
RUN pip install --no-cache-dir -r requirements-searchmedia.txt

COPY searchmedia ./searchmedia

EXPOSE 80

# Module form: "python searchmedia/__main__.py" breaks the package imports.
CMD ["python", "-m", "searchmedia"]
