# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: greenhouse.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10greenhouse.proto\x12\ngreenhouse\"\x8b\x01\n\x0fHumidityControl\x12\x16\n\x0ehumidity_value\x18\x01 \x01(\x02\x12\x15\n\rhumidity_unit\x18\x05 \x01(\t\x12\x14\n\x0cirrigator_on\x18\x02 \x01(\x08\x12\x1b\n\x13irrigator_intensity\x18\x03 \x01(\x05\x12\x16\n\x0eirrigator_unit\x18\x04 \x01(\t\"\xcd\x01\n\x12TemperatureControl\x12\x19\n\x11temperature_value\x18\x01 \x01(\x02\x12\x18\n\x10temperature_unit\x18\x08 \x01(\t\x12\x11\n\theater_on\x18\x02 \x01(\x08\x12\x18\n\x10heater_intensity\x18\x03 \x01(\x05\x12\x13\n\x0bheater_unit\x18\x04 \x01(\t\x12\x11\n\tcooler_on\x18\x05 \x01(\x08\x12\x18\n\x10\x63ooler_intensity\x18\x06 \x01(\x05\x12\x13\n\x0b\x63ooler_unit\x18\x07 \x01(\t\"\xc3\x01\n\x0cLightControl\x12\x13\n\x0blight_value\x18\x01 \x01(\x02\x12\x12\n\nlight_unit\x18\x08 \x01(\t\x12\x11\n\tlights_on\x18\x02 \x01(\x08\x12\x18\n\x10lights_intensity\x18\x03 \x01(\x05\x12\x13\n\x0blights_unit\x18\x04 \x01(\t\x12\x15\n\rcurtains_open\x18\x05 \x01(\x08\x12\x1a\n\x12\x63urtains_intensity\x18\x06 \x01(\x05\x12\x15\n\rcurtains_unit\x18\x07 \x01(\t\"\\\n\x07\x43ommand\x12\x0f\n\x07\x63ommand\x18\x01 \x01(\t\x12\x0f\n\x07\x66\x65\x61ture\x18\x02 \x01(\t\x12\x0e\n\x06\x64\x65vice\x18\x03 \x01(\t\x12\x10\n\x08\x61\x63tuator\x18\x04 \x01(\t\x12\r\n\x05value\x18\x05 \x01(\x02\"z\n\x0c\x44\x65viceStatus\x12\x0e\n\x06\x64\x65vice\x18\x01 \x01(\t\x12\x0f\n\x07\x66\x65\x61ture\x18\x02 \x01(\t\x12\x10\n\x08\x61\x63tuator\x18\x03 \x01(\t\x12\n\n\x02on\x18\x04 \x01(\x08\x12\x0e\n\x06status\x18\x07 \x01(\t\x12\r\n\x05value\x18\x05 \x01(\x02\x12\x0c\n\x04unit\x18\x06 \x01(\t\"O\n\x08Response\x12\x10\n\x08response\x18\x01 \x01(\t\x12\x31\n\x0f\x64\x65vice_statuses\x18\x02 \x03(\x0b\x32\x18.greenhouse.DeviceStatusb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'greenhouse_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _HUMIDITYCONTROL._serialized_start=33
  _HUMIDITYCONTROL._serialized_end=172
  _TEMPERATURECONTROL._serialized_start=175
  _TEMPERATURECONTROL._serialized_end=380
  _LIGHTCONTROL._serialized_start=383
  _LIGHTCONTROL._serialized_end=578
  _COMMAND._serialized_start=580
  _COMMAND._serialized_end=672
  _DEVICESTATUS._serialized_start=674
  _DEVICESTATUS._serialized_end=796
  _RESPONSE._serialized_start=798
  _RESPONSE._serialized_end=877
# @@protoc_insertion_point(module_scope)
