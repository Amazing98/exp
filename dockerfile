FROM python:3
WORKDIR /app
COPY . /app
RUN  pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt 
EXPOSE 3333
CMD ["python3","app.py"]
