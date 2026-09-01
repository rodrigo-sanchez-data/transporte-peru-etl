CREATE TABLE IF NOT EXISTS departamentos (
    id_departamento SERIAL PRIMARY KEY,
    departamento VARCHAR(50) NOT NULL,
    cantidad BIGINT
);

CREATE TABLE IF NOT EXISTS provincias (
    id_provincia SERIAL PRIMARY KEY,
    provincia VARCHAR(50) NOT NULL,
    id_departamento INTEGER REFERENCES departamentos(id_departamento),
    cantidad BIGINT
);

CREATE TABLE IF NOT EXISTS distritos (
    id_distrito SERIAL PRIMARY KEY,
    distrito VARCHAR(50) NOT NULL,
    id_provincia INTEGER REFERENCES provincias(id_provincia),
    cantidad BIGINT
);

CREATE TABLE IF NOT EXISTS siniestros (
    codigo_siniestro VARCHAR(30) PRIMARY KEY,
    fecha_siniestro DATE,
    hora_siniestro VARCHAR(10),
    clase_siniestro VARCHAR(50),
    cantidad_de_fallecidos INTEGER,
    cantidad_de_lesionados INTEGER,
    cantidad_de_vehiculos_danados INTEGER,
    id_distrito INTEGER REFERENCES distritos(id_distrito),
    zona VARCHAR(30),
    coordenadas_latitud FLOAT,
    coordenadas_longitud FLOAT,
    causa_factor_principal VARCHAR(100),
    cod_carretera VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS personas (
    codigo_persona VARCHAR(30) PRIMARY KEY,
    codigo_siniestro VARCHAR(30) REFERENCES siniestros(codigo_siniestro),
    tipo_persona VARCHAR(30),
    gravedad VARCHAR(30),
    edad INTEGER,
    sexo VARCHAR(20),
    posee_licencia VARCHAR(30),
    estado_licencia VARCHAR(50),
    resultado_del_dosaje_etilico_cualitativo VARCHAR(30),
    se_sometio_a_dosaje_etilico_cuantitativo VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS vehiculos (
    codigo_vehiculo VARCHAR(30) PRIMARY KEY,
    codigo_siniestro VARCHAR(30) REFERENCES siniestros(codigo_siniestro),
    vehiculo VARCHAR(50),
    situacion_vehiculo VARCHAR(30),
    posee_seguro VARCHAR(30),
    estado_soat VARCHAR(30),
    modalidad_de_transporte VARCHAR(50)
);