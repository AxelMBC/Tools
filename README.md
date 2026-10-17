# Tools

Lo que uso todos los días y no quiero volver a armar desde cero.

Aquí van scripts que escribí porque una tarea me quitaba tiempo más de una vez, y configuraciones que me tardé en dejar como me gustan. No es un producto ni tiene roadmap. Me funciona a mí, y si a ti te sirve, mejor.

## Lo que hay

### Scripts

| Script | Qué hace | Stack |
|---|---|---|
| [pdf2Mobi](./scripts/pdf2Mobi.py) | Convierte PDFs de clase (columnas laterales, encabezados, notas al pie) en MOBI o AZW3 limpios para Kindle, con portada incluida. | Python, PyMuPDF, Calibre |

### Configuraciones

Todavía nada. Aquí van a ir terminal, editor y lo que me cueste más de una tarde dejar bien.

## Estructura

```
Tools/
├── scripts/    # cosas que se ejecutan
├── configs/    # cosas que se copian o se enlazan
└── README.md
```

La diferencia entre las dos carpetas es simple: un script lo corres, una configuración la instalas. Si algo crece al punto de necesitar varios archivos, se le hace su propia carpeta con su README.

## Reglas

- **Una herramienta, un problema.** Si empieza a hacer dos cosas, son dos herramientas.
- **El `--help` es documentación.** Todo script responde a `-h` con algo útil.
- **Las configuraciones van comentadas.** Dentro de un año no me voy a acordar por qué cambié ese valor.
- **Ningún dato ni secreto va en el repo.** PDFs, libros, tokens, llaves y archivos generados van en el `.gitignore`. Aquí vive lo que hace el trabajo, no lo que procesa.

## Por qué es público

Casi ningún problema que tengo es raro. Seguro alguien más se peleó con un PDF que se ve mal en su Kindle, o lleva tres horas configurando una terminal. Si buscaste en GitHub y llegaste aquí, ojalá te ahorre la tarde que a mí me costó.

---

Hecho en Guadalajara por [Axel Barraza](https://axelbarraza.com).
