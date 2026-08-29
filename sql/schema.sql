CREATE TABLE IF NOT EXISTS departamentos (
    id_departamento SERIAL PRIMARY KEY,
    departamento VARCHAR(50) NOT NULL,
    cantidad BIGINT
);

CREATE TABLE IF NOT EXISTS siniestros (
    c_digo_siniestro VARCHAR(30) PRIMARY KEY,
    fecha_siniestro DATE,
    hora_siniestro VARCHAR(10),
    clase_siniestro VARCHAR(50),
    cantidad_de_fallecidos INTEGER,
    cantidad_de_lesionados INTEGER,
    cantidad_de_vehiculos_da_ados INTEGER,
    id_departamento INTEGER REFERENCES departamentos(id_departamento),
    zona VARCHAR(30),
    coordenadas_latitud FLOAT,
    coordenadas_longitud FLOAT,
    causa_factor_principal VARCHAR(100),
    cod_carretera VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS personas (
    c_digo_persona VARCHAR(30) PRIMARY KEY,
    c_digo_siniestro VARCHAR(30) REFERENCES siniestros(c_digo_siniestro),
    tipo_persona VARCHAR(30),
    gravedad VARCHAR(30),
    edad INTEGER,
    sexo VARCHAR(20),
    posee_licencia VARCHAR(30),
    estado_licencia VARCHAR(50),
    resultado_del_dosaje_et_lico_cualitativo VARCHAR(30),
    se_someti_a_dosaje_et_lico_cuantitativo VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS vehiculos (
    c_digo_vehiculo VARCHAR(30) PRIMARY KEY,
    c_digo_siniestro VARCHAR(30) REFERENCES siniestros(c_digo_siniestro),
    veh_culo VARCHAR(50),
    situaci_n_veh_culo VARCHAR(30),
    posee_seguro VARCHAR(30),
    estado_soat VARCHAR(30),
    modalidad_de_transporte VARCHAR(50)
);

