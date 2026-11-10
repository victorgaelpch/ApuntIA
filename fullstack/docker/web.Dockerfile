# Servicio web de ApuntIA (FULL-13): Nginx sin privilegios que sirve la interfaz estática y
# hace de proxy de la API en el MISMO origen (la cookie de sesión lo necesita y así no hay CORS
# ni nombres de contenedor en el navegador).
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY fullstack/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=nginx:nginx index.html /usr/share/apuntia/index.html
COPY --chown=nginx:nginx front/ /usr/share/apuntia/front/

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/salud || exit 1
