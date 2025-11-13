FROM nginx:stable

# Xóa default config của nginx
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy config + html vào container
COPY conf.default /etc/nginx/conf.d/default.conf
COPY html/ /usr/share/nginx/html/

# Set quyền đọc
RUN chmod -R 755 /usr/share/nginx/html

EXPOSE 80
CMD ["nginx","-g","daemon off;"]
