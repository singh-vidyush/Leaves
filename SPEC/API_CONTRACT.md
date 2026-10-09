# API Contract

<!--
Define the interface between the desktop application and the local FastAPI
backend, including endpoints/operations, request and response shapes, errors,
authentication or local access controls, and versioning.
Recommended boundary: the Tauri shell manages the local FastAPI process; the
frontend calls a loopback-only REST API for backend operations. Use Tauri commands
for native capabilities such as app lifecycle and selected filesystem access.
This keeps indexing and model work in Python while Tauri owns desktop integration.
Tauri documents bundled sidecar processes and local-server IPC patterns:
https://v2.tauri.app/learn/sidecar-nodejs/.

Owner input needed: streaming needs, local security expectations, and the exact
operations and request/response shapes.
-->

<!-- Define endpoint paths and data shapes for dashboard, search, source
management, schedule proposals/writes, and provider sync after the interaction and
approval rules are confirmed. -->
