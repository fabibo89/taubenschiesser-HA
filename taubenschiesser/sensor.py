import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.const import UnitOfPressure

_LOGGER = logging.getLogger(__name__)


from .const import DOMAIN

# --- PlantBot minimal validator (added) ---
def _plantbot_value_is_valid(props, value):
    # Basic empty checks
    if value is None or (isinstance(value, str) and value.strip().lower() in ("", "null", "none")):
        return False
    # Try numeric
    num = None
    try:
        num = float(value)
    except (TypeError, ValueError):
        pass
    # Zero handling
    if props.get("ignore_zero", False) and num == 0.0:
        return False
    # Range handling
    rng = props.get("valid_range")
    if rng and isinstance(rng, (tuple, list)) and num is not None:
        try:
            lo, hi = rng
            if num < lo or num > hi:
                return False
        except Exception:
            pass
    return True
# --- end minimal validator ---


SENSOR_TYPES = {
    
    "temp": {"name": "Temperatur", "unit": UnitOfTemperature.CELSIUS,"device_class":SensorDeviceClass.TEMPERATURE ,"state_class": SensorStateClass.MEASUREMENT, "optional": True,"ignore_zero": True, 'valid_range': (-30.0, 60.0)},
    "hum": {"name": "Feuchtigkeit", "unit": PERCENTAGE,"device_class":SensorDeviceClass.HUMIDITY,"state_class": SensorStateClass.MEASUREMENT, "optional": True,"ignore_zero": True, 'valid_range': (0.0, 100.0)},
    "pressure": {"name": "Luftdruck", "unit": UnitOfPressure.HPA,"device_class":None, "state_class": SensorStateClass.MEASUREMENT,"optional": True,"ignore_zero": True,"icon": "mdi:gauge", 'valid_range': (800.0, 1100.0)},
    "water_level": {"name": "Wasserstand", "unit": PERCENTAGE,"device_class":None,"state_class": SensorStateClass.MEASUREMENT, "optional": True, 'valid_range': (0.0, 100.0)},
    "jobs": {"name": "Jobs", "unit": "count","device_class":None  , "state_class": SensorStateClass.MEASUREMENT,"optional": True,"icon": "mdi:playlist-play","ignore_zero": False},
    "flow": {"name": "Flow", "unit": None,"device_class":None, "state_class": SensorStateClass.TOTAL,"optional": True,"icon": "mdi:water-pump"},
    "lastVolume": {"name": "Volume", "unit": 'ml',"device_class":None ,"state_class": SensorStateClass.MEASUREMENT, "optional": True,"icon": "mdi:water"},
    "status": {"name": "Status", "unit": None,"device_class":None, "optional": False,"icon": "mdi:information"},
    "wifi": {"name": "WIFI", "unit": SIGNAL_STRENGTH_DECIBELS_MILLIWATT,"device_class":SensorDeviceClass.SIGNAL_STRENGTH,"state_class": SensorStateClass.MEASUREMENT, "optional": False, 'valid_range': (-100.0, -20.0)},
    "runtime": {"name": "Runtime", "unit": "min" ,"device_class":SensorDeviceClass.DURATION,"state_class": SensorStateClass.MEASUREMENT, "optional": True, "convert_from_seconds": True},
    "water_runtime": {"name": "Wasser Runtime", "unit": "s" ,"device_class":SensorDeviceClass.DURATION,"state_class": SensorStateClass.MEASUREMENT, "optional": True,"icon": "mdi:timer-sand"},
    "last_reset_reason": {"name": "Letzter Reset Grund", "unit": None, "device_class": None, "optional": True,"icon": "mdi:restart"},
    "memory_usage": {"name": "Speicherauslastung", "unit": None,"device_class": None,"state_class": SensorStateClass.MEASUREMENT, "optional": True,"icon": "mdi:memory"}
}

DYNAMIC_SENSOR_TYPES = {
    "modbusSens_hum": {"name_template": "Bodenfeuchtigkeit MB {addr}", "name_server": "Bodenfeuchtigkeit", "unit": PERCENTAGE, "optional": True, "device_class": SensorDeviceClass.HUMIDITY, "state_class": SensorStateClass.MEASUREMENT, "valid_range": (5.0, 100.0)},
    "modbusSens_temp": {"name_template": "Bodentemperatur MB {addr}", "name_server": "Bodentemperatur", "unit": UnitOfTemperature.CELSIUS, "optional": True, "device_class": SensorDeviceClass.TEMPERATURE, "state_class": SensorStateClass.MEASUREMENT, "ignore_zero": True, "valid_range": (5.0, 100.0)},
    "modbusSens_cond": {"name_template": "Bodenleitfähigkeit MB {addr}", "name_server": "Bodenleitfähigkeit", "unit": "µS/cm", "optional": True, "device_class": None, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:flash"},
    "BTSensoren_temp": {"name_template": "Temperatur BT {mac}", "name_server": "Bodentemperatur", "unit": UnitOfTemperature.CELSIUS, "optional": True, "device_class": SensorDeviceClass.TEMPERATURE, "state_class": SensorStateClass.MEASUREMENT},
    "BTSensoren_hum": {"name_template": "Bodenfeuchtigkeit BT {mac}", "name_server": "Bodenfeuchtigkeit", "unit": PERCENTAGE, "optional": True, "device_class": SensorDeviceClass.HUMIDITY, "state_class": SensorStateClass.MEASUREMENT},
    "BTSensoren_bat": {"name_template": "Batterie BT {mac}", "name_server": "Batterie", "unit": PERCENTAGE, "optional": True, "device_class": SensorDeviceClass.BATTERY, "state_class": SensorStateClass.MEASUREMENT},
    "BTSensoren_con": {"name_template": "Bodenleitfähigkeit BT {mac}", "name_server": "Bodenleitfähigkeit", "unit": "µS/cm", "optional": True, "device_class": None, "state_class": SensorStateClass.MEASUREMENT, "icon": "mdi:flash"},
    "BTSensoren_light": {"name_template": "Licht BT {mac}", "name_server": "Licht", "unit": "lx", "optional": True, "device_class": SensorDeviceClass.ILLUMINANCE, "state_class": SensorStateClass.MEASUREMENT}
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for station_id, station in coordinator.data.items():
        # 1. Feste Sensoren wie bisher
        for key, props in SENSOR_TYPES.items():
            value = station.get(key)
            if not props["optional"] or key in station:
                if props.get('optional', False) and not _plantbot_value_is_valid(props, value):
                    continue
                entities.append(PlantbotSensor(coordinator, station_id, key, props, station.get("name", f"Station {station_id}")))

        # 2. Sensoren aus verschachteltem JSON
        sensoren = station.get("Sensoren", {})

        # Environment-Sensoren
        env = sensoren.get("PlantBot", {})
        for key, value in env.items():
            props = SENSOR_TYPES.get(key)
            if props:
                # Validierung für Environment-Sensoren
                if props.get('optional', False) and not _plantbot_value_is_valid(props, value):
                    continue
                entities.append(PlantbotSensor(coordinator, station_id, f"env_{key}", props, station.get("name", f"Station {station_id}")))

        # Vereinheitlichte Sensor-Erstellung für modbusSens und BTSensoren
        server_sensors = station.get("sensors", {})
        
        sensor_configs = [
            {
                "section": "modbusSens",
                "prefix": "modbusSens", 
                "sensor_types": ["hum", "temp", "cond"],
                "addr_format": "addr"
            },
            {
                "section": "BTSensoren",
                "prefix": "BTSensoren",
                "sensor_types": ["temp", "hum", "bat", "con", "light"], 
                "addr_format": "mac"
            }
        ]
        
        for config in sensor_configs:
            section_data = sensoren.get(config["section"], {})
            sensor_names = {}
            
            # Server-Namen sammeln
            if isinstance(server_sensors, dict):
                server_section = server_sensors.get(config["section"], [])
                # Zuerst sammeln: welche Adressen haben Namen für temp/hum
                address_names = {}
                for sensor_info in server_section:
                    identifier = sensor_info.get("identifier", "")
                    name = sensor_info.get("name", "").strip()
                    address = sensor_info.get("address", "")
                    if identifier.startswith(f"{config['prefix']}_") and name:
                        sensor_type = identifier.replace(f"{config['prefix']}_", "")
                        # Für temp/hum speichern wir den Namen der Adresse
                        if sensor_type in ["temp", "hum"]:
                            address_names[address] = name
                        key = f"{address}_{sensor_type}"
                        sensor_names[key] = name
                
                # Jetzt für alle Adressen mit Namen alle Sensor-Typen ergänzen
                for address, name in address_names.items():
                    for sensor_type in config["sensor_types"]:
                        key = f"{address}_{sensor_type}"
                        if key not in sensor_names:  # Nur wenn noch nicht vorhanden
                            sensor_names[key] = name
            
            # Sensoren erstellen
            for addr, values in section_data.items():
                addr_str = str(addr)
                for sensor_type in config["sensor_types"]:
                    if sensor_type in values:
                        key = f"{config['prefix']}_{sensor_type}_{addr_str}"
                        props = DYNAMIC_SENSOR_TYPES[f"{config['prefix']}_{sensor_type}"].copy()
                        
                        # Server-Name verwenden, wenn vorhanden
                        server_key = f"{addr_str}_{sensor_type}"
                        server_name = sensor_names.get(server_key)
                        if server_name:
                            props["name"] = f"{props['name_server']} {server_name}"
                        else:
                            # Template verwenden
                            if config["addr_format"] == "mac":
                                addr_short = addr_str[-5:] if len(addr_str) >= 5 else addr_str
                                props["name"] = props["name_template"].format(mac=addr_short)
                            else:
                                props["name"] = props["name_template"].format(addr=addr_str)
                        
                        entities.append(PlantbotSensor(coordinator, station_id, key, props, station.get("name", f"Station {station_id}")))
                
    async_add_entities(entities)

class PlantbotSensor(SensorEntity):
    def __init__(self, coordinator, station_id, key, props, station_name):
        self.coordinator = coordinator
        self.station_id = str(station_id)
        self.key = key
        self.station_name = station_name
        #self._attr_name = f"{station_name} – {props['name']}"
        self._attr_name = props['name']
        self._attr_unique_id = f"{station_id}_{key}"
        self._attr_native_unit_of_measurement = props["unit"]
        self._optional = props["optional"]
        self._attr_editable = False  # Das macht's read-only        
        self._attr_device_class = props["device_class"]
        self._attr_state_class = props.get("state_class")
        self.station_ip = coordinator.data[self.station_id].get("ip")
        self._attr_icon = props.get("icon")
        self._props = props
        _LOGGER.debug("##### IP=%s", self.station_ip)


    @property
    def native_value(self):
        if not self.available:
            return None

        station_data = self.coordinator.data[self.station_id]
        sensoren = station_data.get("Sensoren", {})

        # Vereinheitlichte Sensor-Wert-Abfrage für modbusSens und BTSensoren
        value = None
        sensor_configs = [
            {
                "prefixes": ["modbusSens_hum_", "modbusSens_temp_", "modbusSens_cond_"],
                "section": "modbusSens",
                "addr_extraction": lambda key, prefix: key.rsplit("_", 1)[-1],
                "sensor_type_extraction": lambda prefix: prefix.replace("modbusSens_", "").rstrip("_")
            },
            {
                "prefixes": ["BTSensoren_temp_", "BTSensoren_hum_", "BTSensoren_bat_", "BTSensoren_con_", "BTSensoren_light_"],
                "section": "BTSensoren", 
                "addr_extraction": lambda key, prefix: key.replace(prefix, ""),
                "sensor_type_extraction": lambda prefix: prefix.replace("BTSensoren_", "").rstrip("_")
            }
        ]
        
        for config in sensor_configs:
            for prefix in config["prefixes"]:
                if self.key.startswith(prefix):
                    section_data = sensoren.get(config["section"], {})
                    addr = config["addr_extraction"](self.key, prefix)
                    sensor_type = config["sensor_type_extraction"](prefix)
                    value = section_data.get(addr, {}).get(sensor_type)
                    break
            if value is not None:
                break
        
        # Environment-Sensoren (PlantBot)
        if value is None and self.key.startswith("env_"):
            env_key = self.key.replace("env_", "")
            env = sensoren.get("PlantBot", {})
            value = env.get(env_key)
            # Fallback: auch direkt in station_data suchen
            if value is None:
                value = station_data.get(env_key)
        elif value is None:
            value = station_data.get(self.key)

        # Validierung (0 ist erlaubt, sofern ignore_zero=False)
        if not _plantbot_value_is_valid(self._props, value):
            return None

        # Spezielle Umrechnung für bestimmte Sensoren
        if self._props.get("convert_from_seconds", False) and value is not None:
            try:
                # Konvertiere Sekunden zu Minuten
                num = float(value) / 60.0
                return round(num, 1)
            except (TypeError, ValueError):
                pass

        # Zahl zurückgeben, ansonsten den Rohwert
        if isinstance(value, int):
            return value
        try:
            num = float(value)
            return int(num) if num.is_integer() else num
        except (TypeError, ValueError):
            return value

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def device_info(self):
        info = {
            "identifiers": {(DOMAIN, f"station_{self.station_id}")},
            "name": self.station_name,
            "manufacturer": "PlantBot",
            "model": "Bewässerungsstation",
        }
        if self.station_ip:
            info["configuration_url"] = f"http://{self.station_ip}"
        return info

    async def async_update(self):
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        self.coordinator.async_add_listener(self.async_write_ha_state)