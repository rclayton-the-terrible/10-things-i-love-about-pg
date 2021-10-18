# 10 Things I Love About Postgres

1. Rich data model 
 - Native support for arrays
 - User Defined Types

```postgresql
select '{1, 2, 3}'::int[];

create type latlon as (
  latitude float,
  longitude float
);

create table stations
(
	id varchar(5)
		constraint stations_pk
			primary key,
	name varchar(256),
	location latlon,
	services varchar[]
);

insert into stations (id, name, location, services) values
   ('KSAN', 'San Diego', ROW(32.83, -117.13), '{METAR, TAF}'),
   ('KCRQ', 'Carlsbad/Palomar', ROW(33.14, -117.28), '{METAR}'),
   ('KSFO', 'San Francisco Intl Airport', ROW(37.62, -122.37), '{METAR, TAF}'),
   ('KLAX', 'Los Angeles Intl Airport', ROW(33.94, -118.4), '{METAR, TAF}'),
   ('KAVX', 'Catalina Airport (Avalon)', ROW(33.41, -118.42), '{METAR}'),
   ('KSAC', 'Sacramento', ROW(38.52, -121.5), '{METAR, TAF}');

select * from stations where
  'TAF' = any(services)
   and (location).latitude between 33 and 34
   and (location).longitude between -120 and -117;
```

```csv
+----+------------------------+--------------+-----------+
|id  |name                    |location      |services   |
+----+------------------------+--------------+-----------+
|KLAX|Los Angeles Intl Airport|(33.94,-118.4)|{METAR,TAF}|
+----+------------------------+--------------+-----------+
```

- Table Inheritance

```postgresql
create table observation
(
	id bigserial
		constraint observation_pk
			primary key,
	time timestamp with time zone,
	station_id varchar(5)
		constraint observation_stations_id_fk
			references stations
				on delete cascade,
	temperature int,
	dewpoint int,
	wind_dir int,
	wind_speed int,
	wind_gust int,
	altimeter float
);

create table metars
(
    ob_type varchar(5),
    visibility varchar(256),
    clouds varchar(256),
    sig_weather int,
    sea_level_pressure int,
    remarks text
) inherits (observations);

create table asos_obervations (
    ceiling int,
    visibility float,
    precip float
) inherits (observations);

insert into metars
(time, station_id, temperature, dewpoint, wind_dir, wind_speed, wind_gust, altimeter, ob_type, visibility,
 clouds, sig_weather, sea_level_pressure, remarks) values
(now(), 'KSAN', 35, 26, 230, 6, null, 29.99, 'METAR', '7SM', 'SCT030', '', 998, ''),
(now(), 'KSFO', 10, 09, 0, 1, null, 30.02, 'SPECI', '1/2 SM SE-NW 3 SM', 'OVC001', 'FG', 1021, 'CIG001 LOW VIS');

insert into asos_obervations
(time, station_id, temperature, dewpoint, wind_dir, wind_speed, wind_gust, altimeter, ceiling, visibility, altimeter, precip) values
(now(), 'KLAX', 33, 12, 320, 10, 15, 29.98, 200, 10, 29.97, 0),
(now(), 'KSAC', 22, 19, 160, 8, 12, 29.78, 010, 4, 29,78, 0.2);

select tableoid::regclass, station_id, temperature from observation order by temperature desc;
```

```
+----------------+----------+-----------+
|tableoid        |station_id|temperature|
+----------------+----------+-----------+
|metars          |KSAN      |35         |
|asos_obervations|KLAX      |33         |
|asos_obervations|KSAC      |22         |
|metars          |KSFO      |10         |
+----------------+----------+-----------+
```

- Namespaces (Schemas)

```postgresql
create schema ingest;

create table ingest.observations (
    id bigserial
        constraint observations_pk
            primary key,
    station_id varchar(5)
        constraint ingest_observations_stations_id_fk
            references stations
            on delete cascade,
    processed bool default false,
    data text,
    ingested_at timestamp with time zone default now()
);

insert into ingest.observations (station_id, data) values
 ('KSAN', 'KSAN 101651Z 21005KT 10SM CLR 21/13 A3006 RMK AO2 SLP177 T02110128');
```

- Object-Relational Model

```postgresql
select (ROW(0, 'KSAN', true, 'YO', now())::ingest.observations);

create or replace function random_ob_data ()
    returns ingest.observations
as $$
begin
    return ROW(0, 'KSAN', true, 'YO', now())::ingest.observations;
end
$$ LANGUAGE plpgsql;

select random_ob_data();
select (random_ob_data()).station_id;
```

2. JSON

```postgresql

select
    ('{"a":{"b": [{"c":"hello"}]}}'::jsonb) -> 'a' -> 'b' -> 0 -> 'c' as old_access,
    ('{"a":{"b": [{"c":"hello"}]}}'::jsonb)['a']['b'][0]['c'] as access,
    '{"foo":"bar"}'::jsonb ? 'foo' as has_foo_field,
    '{"foo": {"bar":1, "yo":"mama"}}'::jsonb @> '{"foo": { "bar": 1 }}' as path_equal,
    '{"a":1}'::jsonb || '{"b":2}'::jsonb as concat_objects,
    '{"a":1,"b":2}'::jsonb - 'a' as remove_field_a,
    '{"foo": {"bar":1, "yo":"mama"}}'::jsonb #- '{foo,yo}' as remove_by_path;
```

Manipulate JSON:

```postgresql

```

```
+----------+-------+-------------+----------+----------------+--------------+-------------------+
|old_access|access |has_foo_field|path_equal|concat_objects  |remove_field_a|remove_by_path     |
+----------+-------+-------------+----------+----------------+--------------+-------------------+
|"hello"   |"hello"|true         |true      |{"a": 1, "b": 2}|{"b": 2}      |{"foo": {"bar": 1}}|
+----------+-------+-------------+----------+----------------+--------------+-------------------+

```

Convert JSON to records:

```postgresql
select * from json_to_recordset('[{"id": 1}, {"id": 2}, {"id": 3}]'::json) as def(id int);
```

```
+--+
|id|
+--+
|1 |
|2 |
|3 |
+--+
```

```postgresql
select to_json(s) from stations s limit 2;
```

```
+-------------------------------------------------------------------------------------------------------------------+
|to_json                                                                                                            |
+-------------------------------------------------------------------------------------------------------------------+
|{"id":"KSAN","name":"San Diego/Montg","location":{"latitude":32.83,"longitude":-117.13},"services":["METAR","TAF"]}|
|{"id":"KCRQ","name":"Carlsbad/Palomar","location":{"latitude":33.14,"longitude":-117.28},"services":["METAR"]}     |
+-------------------------------------------------------------------------------------------------------------------+
```

3. Common Table Expressions

```postgresql
with
    hot_stations as(
        select station_id from observations where temperature > 30
    ),
    party_stations(id, drinks) as(
        VALUES
            ('KSAN', '{tequila, margaritas}'),
            ('KLAX', '{old fashion, manhattan}'),
            ('KSFO', '{martini, negroni}')
    )
select name, station_id, drinks from stations s
 inner join hot_stations h
            on s.id = h.station_id
 inner join party_stations p
            on s.id = p.id;
```

```
+------------------------+----------+------------------------+
|name                    |station_id|drinks                  |
+------------------------+----------+------------------------+
|San Diego/Montg         |KSAN      |{tequila, margaritas}   |
|Los Angeles Intl Airport|KLAX      |{old fashion, manhattan}|
+------------------------+----------+------------------------+
```

4. Materialized Views

```postgresql
create materialized view hot_party_stations as
with
hot_stations as(
    select station_id from observations where temperature > 30
),
party_stations(id, drinks) as(
    VALUES
      ('KSAN', '{tequila, margaritas}'),
      ('KLAX', '{old fashion, manhattan}'),
      ('KSFO', '{martini, negroni}')
)
select name, station_id, drinks from stations s
    inner join hot_stations h
        on s.id = h.station_id
    inner join party_stations p
        on s.id = p.id;
```

```postgresql
select * from hot_party_stations;
```

```
+------------------------+----------+------------------------+
|name                    |station_id|drinks                  |
+------------------------+----------+------------------------+
|San Diego/Montg         |KSAN      |{tequila, margaritas}   |
|Los Angeles Intl Airport|KLAX      |{old fashion, manhattan}|
+------------------------+----------+------------------------+
```

```postgresql
insert into metars
  (time, station_id, temperature, dewpoint, wind_dir, wind_speed, wind_gust, altimeter,
   ob_type, visibility, clouds, sig_weather, sea_level_pressure, remarks)
values
  (now(), 'KSFO', 37, 26, 180, 6, null, 30.20, 'METAR', '7SM', 'SKC', '', 1012, '');
```

```postgresql
refresh materialized view hot_party_stations;
```

```postgresql
select * from hot_party_stations;
```

```
+--------------------------+----------+------------------------+
|name                      |station_id|drinks                  |
+--------------------------+----------+------------------------+
|San Diego/Montg           |KSAN      |{tequila, margaritas}   |
|San Francisco Intl Airport|KSFO      |{martini, negroni}      |
|Los Angeles Intl Airport  |KLAX      |{old fashion, manhattan}|
+--------------------------+----------+------------------------+
```

8. PL Python

```postgresql
CREATE EXTENSION plpython3u;

create or replace function parse_metar (metar_text text)
    returns metars
AS $$
    from metar import Metar
    obs = Metar.Metar(metar_text)
    return {
      "id": 0,
      "time": obs.time.strftime('%Y-%m-%dT%H:%M:%S%zZ'),
      "station_id": obs.station_id,
      "temperature": int(obs.temp.value()),
      "dewpoint": int(obs.dewpt.value()),
      "wind_dir": int(obs.wind_dir.value()) if obs.wind_dir else None,
      "wind_gust": int(obs.wind_gust.value()) if obs.wind_gust else None,
      "wind_speed": int(obs.wind_speed.value()) if obs.wind_speed else None,
      "altimeter": obs.press.value(),
      "ob_type": obs.type,
      "visibility": obs.vis.value() if obs.vis else None,
      "clouds": "%s" % obs.sky,
      "sig_weather": "%s" % obs.weather,
      "sea_level_pressure": int(obs.press_sea_level.value()) if obs.press_sea_level else None,
      "remarks": obs.remarks(),
    }
$$
    LANGUAGE 'plpython3u';

select station_id, time, temperature, dewpoint
from parse_metar('KSAN 101651Z 21005KT 10SM CLR 21/13 A3006 RMK AO2 SLP177 T02110128');
```

```
+----------+--------------------------+-----------+--------+
|station_id|time                      |temperature|dewpoint|
+----------+--------------------------+-----------+--------+
|KSAN      |2021-10-10 16:51:00.000000|21         |12      |
+----------+--------------------------+-----------+--------+
```

```
station: KSAN
type: routine report, cycle 17 (automatic report)
time: Sun Oct 10 16:51:00 2021
temperature: 21.1 C
dew point: 12.8 C
wind: SSW at 5 knots
visibility: 10 miles
pressure: 1018.0 mb
sky: clear
sea-level pressure: 1017.7 mb
remarks:
- Automated station (type 2)
METAR: KSAN 101651Z 21005KT 10SM CLR 21/13 A3006 RMK AO2 SLP177 T02110128
```

9.  Postgres Foreign Data Wrapper
```postgresql
CREATE EXTENSION http;

SELECT content::json
FROM http_get('https://api.weather.gov/stations/KSAN/observations');

select id, (
  (http_get(
    concat('https://api.weather.gov/stations/', id, '/observations'))).content
  )::json
from stations;

```

Full Text Search

```postgresql
alter table stations add column name_search tsvector;

update stations set name_search = to_tsvector(name)
returning id, name, stations.name_search;
```

```
+----+--------------------------+------------------------------------------+
|id  |name                      |name_search                               |
+----+--------------------------+------------------------------------------+
|KSAN|San Diego/Montg           |'diego/montg':2 'san':1                   |
|KCRQ|Carlsbad/Palomar          |'carlsbad/palomar':1                      |
|KSFO|San Francisco Intl Airport|'airport':4 'francisco':2 'intl':3 'san':1|
|KLAX|Los Angeles Intl Airport  |'airport':4 'angel':2 'intl':3 'los':1    |
|KAVX|Catalina Airport (Avalon) |'airport':2 'avalon':3 'catalina':1       |
|KSAC|Sacramento                |'sacramento':1                            |
+----+--------------------------+------------------------------------------+
```

```postgresql
select * from stations where name_search @@ to_tsquery('san & airport');
```

```
+----+--------------------------+---------------+-----------+------------------------------------------+
|id  |name                      |location       |services   |name_search                               |
+----+--------------------------+---------------+-----------+------------------------------------------+
|KSFO|San Francisco Intl Airport|(37.62,-122.37)|{METAR,TAF}|'airport':4 'francisco':2 'intl':3 'san':1|
+----+--------------------------+---------------+-----------+------------------------------------------+
```

```postgresql
create trigger stations_name_search_update before insert or update
    on stations for each row execute procedure
        tsvector_update_trigger(name_search, 'pg_catalog.english', name);
        
insert into stations (id, name, location, services)
values ('KSBA', 'Santa Barbara', ROW(34.43, -119.85), '{METAR, TAF}')
returning id, name, name_search;
```

```
+----+-------------+---------------------+
|id  |name         |name_search          |
+----+-------------+---------------------+
|KSBA|Santa Barbara|'barbara':2 'santa':1|
+----+-------------+---------------------+
```

```postgresql
select 'This is code demonstrating a feature' as demo;
```

```
+------------------------------------+
|demo                                |
+------------------------------------+
|This is code demonstrating a feature|
+------------------------------------+
```

Geospatial

```postgresql
create extension postgis;

alter table stations add column geom geometry;

select updategeometrysrid('public', 'stations', 'geom', 4269);

update stations
set geom = st_setsrid(
        st_makepoint((stations.location).latitude, (stations.location).longitude),
        4269
    )
returning id, location, geom;
```

```
+----+---------------+--------------------------------------------------+
|id  |location       |geom                                              |
+----+---------------+--------------------------------------------------+
|KSAN|(32.83,-117.13)|0101000020AD1000000AD7A3703D6A4040B81E85EB51485DC0|
|KCRQ|(33.14,-117.28)|0101000020AD10000052B81E85EB91404052B81E85EB515DC0|
|KSFO|(37.62,-122.37)|0101000020AD1000008FC2F5285CCF424048E17A14AE975EC0|
|KLAX|(33.94,-118.4) |0101000020AD100000B81E85EB51F840409A99999999995DC0|
|KAVX|(33.41,-118.42)|0101000020AD10000014AE47E17AB440407B14AE47E19A5DC0|
|KSAC|(38.52,-121.5) |0101000020AD100000C3F5285C8F4243400000000000605EC0|
|KSBA|(34.43,-119.85)|0101000020AD100000D7A3703D0A3741406666666666F65DC0|
+----+---------------+--------------------------------------------------+
```

```postgresql
with myloc(center_point, max_distance_from) as (
    select
                st_setsrid(st_makepoint(33.128756, -117.256752), 4269)
            (50::float / 69::float)::float
)
select
    id,
    name,
    st_distance(geom, m.center_point) * 69 as distance
from stations s
         inner join myloc m on true
where st_dwithin(geom, m.center_point,m.max_distance_from);
```

```
+----+----------------+------------------+
|id  |name            |distance          |
+----+----------------+------------------+
|KSAN|San Diego/Montg |22.39272905046335 |
|KCRQ|Carlsbad/Palomar|1.7818801327358469|
+----+----------------+------------------+
```

Postgres Advisory Locks

```postgresql
select
    pg_try_advisory_xact_lock(42),
    pg_sleep(30),
    pg_advisory_unlock(42);

select pg_try_advisory_xact_lock(42);
```

Listen+Notify

```typescript
import { Client } from 'pg';

async function main() {
  const client = new Client({
    user: 'postgres',
    password: '10thingsloveaboutpg',
    host: 'localhost',
    database: 'weather',
  });

  client.on('notification', (data) => {
    console.log('Notification:', data);
  });

  await client.connect();

  await client.query('LISTEN observations');
}

main().catch(console.error)
```

```postgresql
select pg_notify('observations', 'hello');
```

```postgresql
create or replace function notify_new_observation()
    returns trigger
as $$
    begin
    perform pg_notify('observations', new.id::varchar);
    return null;
    end
$$ language plpgsql;

create trigger metar_notify_on_create after insert
    on metars for each row execute procedure
        notify_new_observation();

create trigger asos_observations_notify_on_create after insert
    on asos_obervations for each row execute procedure
        notify_new_observation();
```

```postgresql
insert into metars
  (time, station_id, temperature, dewpoint, wind_dir, wind_speed, wind_gust, altimeter,
   ob_type, visibility, clouds, sig_weather, sea_level_pressure, remarks)
values
  (now(), 'KSBA', 21, 16, 240, 8, 16, 29.12, 'METAR', '7SM', 'SKC', '', 998, '')
  returning id;
```

```
+--+
|id|
+--+
|7 |
+--+
```


