# Validación cruzada de la búsqueda

Pieza opcional. Responde a la pregunta de cómo se comprueba que la búsqueda automática recuperó lo mismo que una búsqueda hecha a mano.

1. Se imprime la cadena exacta de una base y una ecuación con `cadenas.py mostrar`.
2. Una persona abre la base en el navegador, pega la cadena, aplica el filtro de años del protocolo y anota el número de resultados, la fecha y la hora, y los campos en que buscó la interfaz.
3. Se corre la misma búsqueda con `buscar.py --solo-contar` y se anota lo mismo.
4. Se agrega una fila a `01_busqueda/validacion.csv` con la base, la ecuación, los dos números y la causa de la diferencia.

El criterio no es que los números coincidan, sino que la diferencia quede explicada. Las causas habituales son tres: la interfaz busca en todos los campos y la conexión programática en título y resumen; la fuente cuenta tipos de documento que la interfaz filtra sin avisar; o la base indexó registros nuevos entre una consulta y otra. Una diferencia sin explicación quiere decir que la cadena no es la misma, y se corrige antes de seguir.
