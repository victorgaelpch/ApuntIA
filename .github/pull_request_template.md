## Issue

Closes #

## Qué cambia

<!-- Resumen breve: qué se hizo y por qué. -->

## Cómo se comprobó

<!-- Comandos ejecutados, capturas o ejemplos de petición/respuesta. -->

## Definición de Hecho (fullstack/docs/definicion-de-hecho.md)

- [ ] La rama sale de `main`, se llama `<area>-<nn>-<descripcion>` y solo contiene este issue.
- [ ] Los commits siguen Conventional Commits y referencian el issue (`CONTRIBUTING.md`).
- [ ] Cumple **todos** los criterios de aceptación del issue.
- [ ] La CI está en verde (o `fullstack/scripts/validar.sh --completo` en local).
- [ ] Si cambia el contrato de la API: `fullstack/docs/api.md` o `fullstack/docs/api-v2.md`, `front/js/api-mock.js` y las pruebas se actualizan en este mismo PR.
- [ ] Documentación actualizada (README, README del área o `fullstack/docs/`); los comandos nuevos se ejecutaron tal como están escritos y los enlaces pasan `python fullstack/scripts/comprobar_enlaces.py`.
- [ ] Si cambia el OCR o el PDF: `python fullstack/evaluacion/evaluar.py --comparar fullstack/evaluacion/linea-base.json` sin regresiones (y la línea base actualizada si mejora).
- [ ] Sin credenciales, claves ni rutas de una computadora concreta en el código.
- [ ] Revisado y aprobado por al menos **un** integrante que no sea el autor.
