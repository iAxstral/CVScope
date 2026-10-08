from app.services.anonimizador import anonimizar

CV = (
    "María José Pérez Gómez. Ingeniera de Software en Medellín. "
    "Nacida el 3 de mayo de 1995. Estado civil: soltera. "
    "Tel: +57 300 123 4567, maria.perez@gmail.com, linkedin.com/in/mjperez. CC 1.020.304.050. "
    "Perfil: 6 años de experiencia. Desarrolladora con React y Node.js."
)


def test_elimina_datos_personales():
    texto = anonimizar(CV, "María José Pérez Gómez")
    for dato in ["María", "Pérez", "Medellín", "1995", "soltera", "300 123", "gmail", "linkedin", "1.020"]:
        assert dato not in texto
    for marca in ["[CANDIDATO]", "[CIUDAD]", "[EMAIL]", "[URL]", "[TELEFONO]", "[DOCUMENTO]", "[DATO PERSONAL]"]:
        assert marca in texto


def test_conserva_lo_relevante_para_el_cargo():
    texto = anonimizar(CV)
    assert "6 años de experiencia" in texto
    assert "React" in texto and "Node.js" in texto


def test_neutraliza_el_genero_de_las_profesiones():
    assert anonimizar("Ingeniera de datos. Desarrolladora.") == anonimizar("Ingeniero de datos. Desarrollador.")
    assert "ingenierx" in anonimizar("Trabajé con ingenieros y jefes.")


def test_mismo_cv_con_otro_nombre_y_ciudad_queda_igual():
    a = "Ana Ruiz. Profesional en ventas en Cali. 5 años de experiencia en ventas B2B con HubSpot."
    b = "Pedro Gómez. Profesional en ventas en Bogotá. 5 años de experiencia en ventas B2B con HubSpot."
    assert anonimizar(a) == anonimizar(b)


def test_ciudades_con_y_sin_tilde():
    for ciudad in ["Quibdó", "Quibdo", "San José del Guaviare", "Itagüí", "Tumaco", "BOGOTA"]:
        assert ciudad not in anonimizar(f"Vivo en {ciudad}. 3 años de experiencia."), ciudad
