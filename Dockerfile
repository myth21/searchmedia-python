FROM python:3.12-slim

WORKDIR /var/www

ENV PYTHONUNBUFFERED=1

COPY requirements-searchmedia.txt .
RUN pip install --no-cache-dir -r requirements-searchmedia.txt

COPY searchmedia ./searchmedia

EXPOSE 80

CMD ["python", "-m", "searchmedia"]
