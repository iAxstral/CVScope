import numpy as np
import pytest

from app.services.red_competitiva.competitiva import maxnet, probabilidades


@pytest.mark.parametrize("semilla", range(20))
def test_gana_la_neurona_con_mayor_fuerza(semilla):
    fuerzas = np.random.default_rng(semilla).normal(size=12) * 3
    resultado = maxnet(fuerzas)
    assert resultado["ganador"] == int(np.argmax(fuerzas))


def test_al_final_solo_queda_una_neurona_activa():
    resultado = maxnet([1.0, 3.0, 2.0, 0.5])
    final = resultado["trayectoria"][-1]
    assert np.count_nonzero(final) == 1
    assert resultado["iteraciones"] == len(resultado["trayectoria"]) - 1


def test_la_inhibicion_nunca_aumenta_activaciones():
    trayectoria = maxnet([0.2, 1.4, 1.1, 0.9])["trayectoria"]
    for antes, despues in zip(trayectoria, trayectoria[1:]):
        assert np.all(despues <= antes + 1e-12)


def test_duelo_coincide_con_sigmoide_de_la_diferencia():
    s_a, s_b = 1.7, 0.4
    p = probabilidades([s_a, s_b])
    assert p[0] == pytest.approx(1 / (1 + np.exp(-(s_a - s_b))))
    assert p.sum() == pytest.approx(1.0)


def test_empate_exacto_gana_la_primera_sembrada_sin_ciclo_infinito():
    resultado = maxnet([2.0, 2.0])
    assert resultado["ganador"] == 0
    assert resultado["iteraciones"] == 0


def test_epsilon_fuera_de_rango():
    with pytest.raises(ValueError):
        maxnet([1.0, 2.0, 3.0], epsilon=0.6)  # máximo 1 / (3 - 1) = 0.5
