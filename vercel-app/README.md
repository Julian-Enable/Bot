# Contrib Bot (Vercel) — GitHub App template

Plantilla mínima para desplegar en Vercel una página que, usando un GitHub App, haga commits en una repo objetivo sin que tengas que gestionar PATs manualmente. Mantén tu racha de contribuciones verde sin tocar tu código de producción.

## 📁 Archivos clave
- `pages/api/commit.js` — endpoint serverless que crea/actualiza `contributions/keep_alive.md` en la repo objetivo (máx 7 commits/día).
- `pages/api/status.js` — endpoint que muestra la última fecha de commit.
- `lib/githubApp.js` — utilidades para crear JWT y pedir token de instalación.
- `pages/index.js` — frontend mínimo con botón "Commit ahora".

---

## 🚀 Guía completa: De cero a tu primer commit

### Paso 1: Crear la GitHub App (hazlo una sola vez)

1. **Ve a GitHub Settings**:
   - Abre https://github.com/settings/apps
   - O navega: tu perfil → Settings → Developer settings (menú izquierdo) → GitHub Apps → **New GitHub App**

2. **Completa el formulario**:
   - **GitHub App name**: `contrib-bot` (o el nombre que prefieras, debe ser único)
   - **Homepage URL**: Cualquier URL (puede ser `https://github.com/tuUsuario` o la URL de Vercel cuando la tengas)
   - **Callback URL**: deja en blanco (no usamos OAuth de usuarios)
   - **Webhook**: desmarca "Active" (no necesitamos webhooks)
   - **Permissions** → Repository permissions:
     - **Contents**: selecciona `Read and write` (necesario para crear commits)
   - **Where can this GitHub App be installed?**: selecciona `Only on this account`

3. **Crea la App**:
   - Haz clic en **Create GitHub App**
   - Serás redirigido a la página de configuración de tu nueva App

4. **Obtén el App ID**:
   - En la página de configuración, verás el **App ID** cerca del nombre (ejemplo: `123456`)
   - **Cópialo** — lo necesitarás para Vercel

5. **Genera la clave privada**:
   - En la misma página, busca la sección **Private keys**
   - Haz clic en **Generate a private key**
   - Se descargará un archivo `.pem` (por ejemplo `contrib-bot.2025-11-04.private-key.pem`)
   - **Guárdalo en un lugar seguro** — lo necesitarás para Vercel

6. **Instala la App en tu repositorio objetivo**:
   - En el menú izquierdo, haz clic en **Install App**
   - Selecciona tu cuenta
   - Elige **Only select repositories** y selecciona el repositorio donde quieres hacer los commits (puede ser este mismo repo `Bot` u otro que crees específicamente)
   - Haz clic en **Install**

✅ **Listo**: tienes tu GitHub App creada e instalada.

---

### Paso 2: Subir el código a GitHub (si no lo has hecho)

1. **Inicializa git** (si no lo hiciste):
```powershell
cd c:\Users\Desktop\Documents\Julian\GitHub\Bot
git init
git add .
git commit -m "Initial commit: contrib bot con GitHub App"
```

2. **Crea un repo en GitHub**:
   - Ve a https://github.com/new
   - Nombre: `Bot` (o el que prefieras)
   - Público o privado (tu elección)
   - No inicialices con README (ya tienes código)
   - Crea el repositorio

3. **Sube el código**:
```powershell
git remote add origin https://github.com/tuUsuario/Bot.git
git branch -M main
git push -u origin main
```

---

### Paso 3: Desplegar a Vercel

1. **Ve a Vercel**:
   - Abre https://vercel.com
   - Inicia sesión (puedes usar tu cuenta de GitHub)

2. **Importa tu proyecto**:
   - En el dashboard, haz clic en **Add New...** → **Project**
   - Conecta tu cuenta de GitHub si es necesario
   - Busca y selecciona tu repositorio `Bot`
   - Haz clic en **Import**

3. **Configura el proyecto**:
   - **Framework Preset**: Vercel detectará automáticamente Next.js
   - **Root Directory**: cambia a `vercel-app` (haz clic en **Edit** y escribe `vercel-app`)
   - **Build Command**: deja el valor por defecto (`next build`)
   - **Output Directory**: deja el valor por defecto (`.next`)

4. **NO hagas clic en Deploy todavía** — primero configura las variables de entorno

---

### Paso 4: Configurar variables de entorno en Vercel

1. **En la página de configuración del proyecto** (antes de Deploy), expande **Environment Variables**

2. **Añade estas variables** (haz clic en el primer campo para añadir):

   | Key | Value | Notas |
   |-----|-------|-------|
   | `APP_ID` | `123456` | El App ID que copiaste de GitHub |
   | `PRIVATE_KEY` | *contenido del .pem* | Ver instrucciones abajo ⬇️ |
   | `TARGET_REPO` | `tuUsuario/Bot` | Formato: `owner/repo` |
   | `COMMIT_NAME` | `Tu Nombre` | Tu nombre real |
   | `COMMIT_EMAIL` | `tu@email.com` | Email verificado en GitHub |
   | `BOT_BRANCH` | `contrib-bot` | Opcional (por defecto `contrib-bot`) |
   | `INVOCATION_SECRET` | `miSecreto123` | Opcional pero recomendado |

3. **Cómo pegar PRIVATE_KEY** (importante):
   - Abre el archivo `.pem` con un editor de texto (Notepad, VS Code)
   - Verás algo como:
   ```
   -----BEGIN RSA PRIVATE KEY-----
   MIIEpAIBAAKCAQEA...
   ... muchas líneas ...
   -----END RSA PRIVATE KEY-----
   ```
   - **Opción A** (recomendada): Copia todo el contenido incluyendo las líneas `-----BEGIN` y `-----END` y pégalo directamente en Vercel. Si Vercel acepta múltiples líneas, listo.
   - **Opción B**: Si Vercel solo acepta una línea, reemplaza cada salto de línea con `\n`. Ejemplo:
   ```
   -----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----\n
   ```
   El código lo convertirá automáticamente.

4. **Selecciona los entornos**:
   - Marca: **Production**, **Preview**, **Development** (o solo Production si prefieres)

5. **Haz clic en Deploy** 🚀

---

### Paso 5: Usar el bot

1. **Espera a que termine el deployment**:
   - Vercel mostrará el progreso y te dará una URL (ejemplo: `https://bot-abc123.vercel.app`)

2. **Abre la URL**:
   - Verás la página con el título "Contrib Bot (Vercel)"
   - Un campo para pegar el `INVOCATION_SECRET` (si lo configuraste)
   - Un botón "Commit ahora"
   - La sección "Estado" mostrará la última entrada (o null si es la primera vez)

3. **Pega tu INVOCATION_SECRET** (si lo configuraste):
   - En el campo "Invocation secret (X-APP-KEY)", pega el valor que pusiste en Vercel (ejemplo: `miSecreto123`)

4. **Haz clic en "Commit ahora"**:
   - El botón dirá "Enviando..."
   - Después de unos segundos verás la respuesta JSON con `"ok": true`
   - La sección "Estado" se actualizará mostrando la última línea con la fecha

5. **Verifica en GitHub**:
   - Ve a tu repositorio objetivo (el que pusiste en `TARGET_REPO`)
   - Busca la rama `contrib-bot` (o el nombre que pusiste en `BOT_BRANCH`)
   - Verás un archivo `contributions/keep_alive.md` con una línea timestamped
   - El commit aparecerá en tu gráfico de contribuciones si usaste tu email verificado

---

## 🎯 Uso diario

- **Una vez al día**: abre la URL de Vercel y pulsa "Commit ahora"
- **Automatización opcional**: puedes crear un cron job que llame al endpoint `/api/commit` con el header `X-APP-KEY`

Ejemplo con curl (Windows PowerShell):
```powershell
curl.exe -X POST https://bot-abc123.vercel.app/api/commit -H "X-APP-KEY: miSecreto123"
```

O con un servicio como [cron-job.org](https://cron-job.org) configurado para llamar a tu endpoint diariamente.

---

## 🔒 Seguridad

- ✅ La `PRIVATE_KEY` está segura en Vercel (variables de entorno cifradas)
- ✅ El `INVOCATION_SECRET` evita que cualquiera abuse del endpoint
- ✅ Rate-limit de 7 commits/día para prevenir uso excesivo
- ✅ Los commits van a una rama separada (`contrib-bot`) sin tocar tu código de producción
- ✅ Anti-duplicados: no crea más de un commit por día (UTC)

---

## ❓ Troubleshooting

**Error: "Installation not found for repo"**
- Verifica que instalaste la GitHub App en el repositorio correcto
- Ve a https://github.com/settings/installations y confirma que está instalada

**Error: "Failed to create installation token"**
- Verifica que `APP_ID` y `PRIVATE_KEY` sean correctos
- Verifica que diste permisos de `Contents: Read & Write` a la App

**Error: "Unauthorized (missing X-APP-KEY)"**
- Si configuraste `INVOCATION_SECRET`, debes pegarlo en el campo de la UI
- O quita esa variable de entorno en Vercel si no quieres protección

**Los commits no aparecen en mi perfil**
- Verifica que `COMMIT_EMAIL` esté verificado en tu cuenta de GitHub
- Ve a https://github.com/settings/emails y confirma el email

**"Rate limit: max 7 commits per day reached"**
- Espera al día siguiente (UTC) o redespliega en Vercel para resetear el contador

---

## 🎨 Próximas mejoras opcionales

- [ ] Formatear fecha de forma legible en la UI
- [ ] Guardar `INVOCATION_SECRET` en localStorage del navegador
- [ ] Añadir un botón "Refresh status" sin hacer commit
- [ ] Dashboard con historial de commits
- [ ] Soporte para múltiples repos objetivo

---

## 📝 Resumen

✅ **GitHub App** creada e instalada  
✅ **Código** desplegado en Vercel  
✅ **Variables de entorno** configuradas  
✅ **Bot** listo para mantener tu racha verde  

**Próximo paso**: abre tu URL de Vercel y haz tu primer commit 🎉
