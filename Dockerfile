FROM python:3.8-slim
WORKDIR /app
COPY main.py /app/
RUN pip install requests beautifulsoup4 aiogram
CMD ["python", "main.py", "categories.py", "discount_wrapper.py", "maxima_scrapper.py", "search_service.py"]