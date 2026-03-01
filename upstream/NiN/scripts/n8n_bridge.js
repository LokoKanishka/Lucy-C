#!/usr/bin/env node
/**
 * n8n_bridge.js — Puente entre Antigravity y la API de n8n
 * 
 * Se ejecuta DENTRO del container n8n-lucy via:
 *   docker exec -e N8N_API_KEY=... n8n-lucy node /home/lucy-ubuntu/Escritorio/NIN/scripts/n8n_bridge.js <cmd> [args...]
 * 
 * Comandos:
 *   list                          — Lista workflows (id, name, active)
 *   get <id>                      — Obtiene workflow completo
 *   update <id> <json_path>       — Actualiza workflow desde archivo JSON
 *   create <json_path>            — Crea workflow desde archivo JSON
 *   delete <id>                   — Elimina workflow
 *   activate <id>                 — Activa workflow (PUT active:true)
 *   deactivate <id>               — Desactiva workflow
 *   execute <id> [json_input]     — Ejecuta workflow con input
 *   executions [workflow_id]      — Lista últimas ejecuciones
 *   test-connection               — Verifica conexión con la API
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const API_KEY = process.env.N8N_API_KEY;
const API_BASE = '/api/v1';
const HOST = 'localhost';
const PORT = 5678;

if (!API_KEY) {
    console.log(JSON.stringify({ error: 'N8N_API_KEY not set' }));
    process.exit(1);
}

function apiRequest(method, apiPath, body = null, stripHeavy = false) {
    return new Promise((resolve, reject) => {
        const data = body ? JSON.stringify(body) : null;
        const headers = {
            'Accept': 'application/json',
            'X-N8N-API-KEY': API_KEY,
        };
        if (data) {
            headers['Content-Type'] = 'application/json';
            headers['Content-Length'] = Buffer.byteLength(data);
        }

        const req = http.request({
            hostname: HOST, port: PORT, path: `${API_BASE}${apiPath}`,
            method, headers, timeout: 55000
        }, res => {
            const chunks = [];
            res.on('data', c => chunks.push(c));
            res.on('end', () => {
                try {
                    let parsed = JSON.parse(Buffer.concat(chunks).toString());
                    if (stripHeavy && parsed && typeof parsed === 'object') {
                        delete parsed.activeVersion;
                        delete parsed.shared;
                        delete parsed.staticData;
                        delete parsed.pinData;
                        delete parsed.tags;
                    }
                    resolve({ status: res.statusCode, data: parsed });
                } catch (e) {
                    resolve({ status: res.statusCode, data: Buffer.concat(chunks).toString().substring(0, 2000) });
                }
            });
        });

        req.on('timeout', () => { req.destroy(); reject(new Error('Request timed out (55s)')); });
        req.on('error', reject);
        if (data) req.write(data);
        req.end();
    });
}

async function main() {
    const args = process.argv.slice(2);
    const cmd = args[0];

    if (!cmd) {
        console.log(JSON.stringify({ error: 'No command specified. Use: list, get, update, create, delete, activate, deactivate, execute, executions, test-connection' }));
        process.exit(1);
    }

    try {
        let result;

        switch (cmd) {
            case 'test-connection': {
                result = await apiRequest('GET', '/workflows?limit=1');
                const count = (result.data.data || result.data).length;
                console.log(JSON.stringify({ ok: true, status: result.status, message: `Connected. Found workflows.` }));
                break;
            }

            case 'list': {
                result = await apiRequest('GET', '/workflows');
                const workflows = (result.data.data || result.data);
                const summary = workflows.map(w => ({
                    id: w.id, name: w.name, active: w.active,
                    updatedAt: w.updatedAt
                }));
                console.log(JSON.stringify({ ok: true, workflows: summary }));
                break;
            }

            case 'inspect': {
                // Lightweight: strips heavy fields, only returns node summary
                const id = args[1];
                if (!id) { console.log(JSON.stringify({ error: 'Usage: inspect <workflow_id>' })); process.exit(1); }
                result = await apiRequest('GET', `/workflows/${id}`, null, true);
                const wf = result.data;
                const nodes = (wf.nodes || []).map(n => ({
                    id: n.id, name: n.name, type: n.type,
                    params: n.parameters
                }));
                console.log(JSON.stringify({
                    ok: true, id: wf.id, name: wf.name, active: wf.active,
                    nodeCount: nodes.length, nodes,
                    connectionKeys: Object.keys(wf.connections || {})
                }));
                break;
            }

            case 'get': {
                const id = args[1];
                if (!id) { console.log(JSON.stringify({ error: 'Usage: get <workflow_id>' })); process.exit(1); }
                result = await apiRequest('GET', `/workflows/${id}`, null, true);
                console.log(JSON.stringify({ ok: true, workflow: result.data }));
                break;
            }

            case 'update': {
                const id = args[1];
                const jsonPath = args[2];
                if (!id || !jsonPath) { console.log(JSON.stringify({ error: 'Usage: update <workflow_id> <json_path>' })); process.exit(1); }
                const wfData = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
                result = await apiRequest('PUT', `/workflows/${id}`, wfData);
                const updatedName = result.data.name || 'unknown';
                console.log(JSON.stringify({ ok: result.status === 200, status: result.status, name: updatedName, id }));
                break;
            }

            case 'create': {
                const jsonPath = args[1];
                if (!jsonPath) { console.log(JSON.stringify({ error: 'Usage: create <json_path>' })); process.exit(1); }
                const wfData = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
                result = await apiRequest('POST', '/workflows', wfData);
                const newId = result.data.id || null;
                const newName = result.data.name || 'unknown';
                console.log(JSON.stringify({ ok: result.status === 200, status: result.status, id: newId, name: newName }));
                break;
            }

            case 'delete': {
                const id = args[1];
                if (!id) { console.log(JSON.stringify({ error: 'Usage: delete <workflow_id>' })); process.exit(1); }
                result = await apiRequest('DELETE', `/workflows/${id}`);
                console.log(JSON.stringify({ ok: result.status === 200, status: result.status, id }));
                break;
            }

            case 'activate': {
                const id = args[1];
                if (!id) { console.log(JSON.stringify({ error: 'Usage: activate <workflow_id>' })); process.exit(1); }
                result = await apiRequest('PUT', `/workflows/${id}`, { active: true });
                console.log(JSON.stringify({ ok: result.status === 200, status: result.status, id, active: true }));
                break;
            }

            case 'deactivate': {
                const id = args[1];
                if (!id) { console.log(JSON.stringify({ error: 'Usage: deactivate <workflow_id>' })); process.exit(1); }
                result = await apiRequest('PUT', `/workflows/${id}`, { active: false });
                console.log(JSON.stringify({ ok: result.status === 200, status: result.status, id, active: false }));
                break;
            }

            case 'execute': {
                const id = args[1];
                const inputJson = args[2] || '{}';
                if (!id) { console.log(JSON.stringify({ error: 'Usage: execute <workflow_id> [json_input]' })); process.exit(1); }
                const input = JSON.parse(inputJson);
                // Use the internal webhook approach for sub-workflow execution
                // or the /executions endpoint
                result = await apiRequest('POST', `/workflows/${id}/run`, input);
                console.log(JSON.stringify({ ok: result.status >= 200 && result.status < 300, status: result.status, result: result.data }));
                break;
            }

            case 'executions': {
                const wfId = args[1];
                const qPath = wfId ? `/executions?workflowId=${wfId}&limit=5` : '/executions?limit=5';
                result = await apiRequest('GET', qPath);
                const execs = result.data.data || result.data;
                const summary = Array.isArray(execs) ? execs.map(e => ({
                    id: e.id, status: e.status, finished: e.finished,
                    startedAt: e.startedAt, workflowName: e.workflowData?.name
                })) : execs;
                console.log(JSON.stringify({ ok: true, executions: summary }));
                break;
            }

            default:
                console.log(JSON.stringify({ error: `Unknown command: ${cmd}` }));
                process.exit(1);
        }
    } catch (err) {
        console.log(JSON.stringify({ error: err.message }));
        process.exit(1);
    }
}

main();
