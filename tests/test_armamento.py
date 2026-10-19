import armamento
import tablero


def test_catalogo_tiene_las_siete_armas_con_sus_datos():
    assert sorted(armamento.CATALOGO_ARMAS) == ["C", "G", "L", "O", "R", "S", "T"]
    for arma in armamento.CATALOGO_ARMAS.values():
        assert "nombre" in arma
        assert "municion_inicial" in arma
        assert "funcion" in arma


def test_torpedo_tiene_municion_ilimitada():
    assert armamento.CATALOGO_ARMAS["T"]["municion_inicial"] is None


def test_torpedo_afecta_solo_la_celda_apuntada():
    cubo = tablero.crear_cubo(8)
    funcion = armamento.CATALOGO_ARMAS["T"]["funcion"]
    assert funcion(cubo, (4, 2, 7)) == [(4, 2, 7)]
    assert tablero.contar_celdas_en_estado(cubo, tablero.SIN_EXPLORAR) == 512
