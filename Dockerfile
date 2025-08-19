FROM python:3.13.6

WORKDIR /currency_exchange

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh
#CMD ["tail", "-f", "/dev/null"]
CMD ["./entrypoint.sh"]
