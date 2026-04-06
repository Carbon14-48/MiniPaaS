FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Monte le socket Docker pour pouvoir exécuter docker tag / docker push
# docker:local://localhost:5000/<image>
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
