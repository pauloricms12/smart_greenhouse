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




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10greenhouse.proto\x12\ngreenhouse\">\n\x12\x44\x65viceRegistration\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04type\x18\x02 \x01(\t\x12\x0c\n\x04port\x18\x03 \x01(\x05\"6\n\x14ResponseRegistration\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0e\n\x06\x64\x65vice\x18\x02 \x01(\t\"\\\n\x07\x43ommand\x12\x0f\n\x07\x63ommand\x18\x01 \x01(\t\x12\x0f\n\x07\x66\x65\x61ture\x18\x02 \x01(\t\x12\x0e\n\x06\x64\x65vice\x18\x03 \x01(\t\x12\x10\n\x08\x61\x63tuator\x18\x04 \x01(\t\x12\r\n\x05value\x18\x05 \x01(\x02\"z\n\x0c\x44\x65viceStatus\x12\x0e\n\x06\x64\x65vice\x18\x01 \x01(\t\x12\x0f\n\x07\x66\x65\x61ture\x18\x02 \x01(\t\x12\x10\n\x08\x61\x63tuator\x18\x03 \x01(\t\x12\n\n\x02on\x18\x04 \x01(\x08\x12\x0e\n\x06status\x18\x07 \x01(\t\x12\r\n\x05value\x18\x05 \x01(\x02\x12\x0c\n\x04unit\x18\x06 \x01(\t\"M\n\x08Response\x12\x10\n\x08response\x18\x01 \x01(\t\x12/\n\rdevice_status\x18\x02 \x03(\x0b\x32\x18.greenhouse.DeviceStatusb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'greenhouse_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _DEVICEREGISTRATION._serialized_start=32
  _DEVICEREGISTRATION._serialized_end=94
  _RESPONSEREGISTRATION._serialized_start=96
  _RESPONSEREGISTRATION._serialized_end=150
  _COMMAND._serialized_start=152
  _COMMAND._serialized_end=244
  _DEVICESTATUS._serialized_start=246
  _DEVICESTATUS._serialized_end=368
  _RESPONSE._serialized_start=370
  _RESPONSE._serialized_end=447
# @@protoc_insertion_point(module_scope)
