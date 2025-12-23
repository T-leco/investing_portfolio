![Investing Portfolio Logo](logos/logo@2x.png)

<p align="center">
<img src="https://img.shields.io/badge/HACS-Custom-orange.svg">
<img src="https://img.shields.io/maintenance/yes/2025.svg">
<img src="https://img.shields.io/badge/version-1.0.0-blue">
<a href="https://github.com/T-leco/investing_portfolio/issues"><img alt="Issues" src="https://img.shields.io/github/issues/T-leco/investing_portfolio?color=0088ff"></a>
<a href="https://www.buymeacoffee.com/teleco"><img alt="Invítame a un café" src="https://img.shields.io/badge/support-buymeacoffee?logo=buymeacoffee&logoColor=black&color=%23FFDD00"></a>
</p>

<p align="center" style="font-weight:bold">
  🚀 Sigue tus inversiones directamente desde Home Assistant.
</p>

<br>

Toma el control total de tus finanzas integrando tus carteras de [Investing.com](https://www.investing.com/) en tu hogar inteligente. Esta integración te permite visualizar en tiempo real el valor de tus acciones, criptomonedas y fondos, permitiéndote crear automatizaciones potentes y paneles espectaculares basados en tu patrimonio y rendimiento diario.

> [!IMPORTANT]
> Esta integración utiliza el **endpoint oficial de la API** que usa la aplicación móvil de Investing.com. **No realiza web scraping**, lo que garantiza una mayor fiabilidad y velocidad.


## ✨ Características

- **Soporte para múltiples portfolios**: Añade varias carteras como entradas separadas.
- **Entidades dinámicas**: Las entidades usan el nombre del portfolio (ej: `sensor.investing_cesar`).
- **Registro de dispositivos**: Todas las entidades aparecen agrupadas bajo un dispositivo "Investing {Cartera}" en la UI.
- **Sensores completos**: Capital invertido, cambio total, cambio diario, porcentajes.
- **Actualización manual**: Botón para forzar la actualización de datos de cada portfolio.
- **Actualizaciones configurables**: Establece horarios de actualización mediante las opciones.
- **Notificaciones de error**: Recibe alertas por tokens expirados o problemas.
- **Optimizado para Home Assistant**: Usa la sesión compartida de HA para mayor eficiencia.

## ✅ Prerrequisitos

- Home Assistant instalado (2023.8.0 o superior).
- [HACS](https://hacs.xyz/) instalado (para el método de instalación recomendado).
- Una cuenta en [Investing.com](https://www.investing.com/).

## Instalación

La forma más fácil es via [HACS](https://hacs.xyz/):

[![Abre tu instancia de Home Assistant y abre el repositorio en HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=T-leco&repository=investing_portfolio&category=integration)

`HACS -> Integraciones -> Explorar y añadir repositorios -> Investing Portfolio`

> [!NOTE]
> HACS no "configura" la integración automáticamente. Después de instalar via HACS, ve a **Ajustes → Dispositivos y servicios → Añadir integración** y busca "Investing Portfolio".

### Instalación Manual

1. Descarga la última versión desde [GitHub Releases](https://github.com/T-leco/investing_portfolio/releases).
2. Extrae la carpeta `custom_components/investing_portfolio`.
3. Copia esta carpeta a tu directorio de configuración de Home Assistant:
   ```
   /config/custom_components/investing_portfolio/
   ```
   La carpeta `config` es donde se encuentra tu archivo `configuration.yaml`.
4. Reinicia Home Assistant.

### Configuración

1. Ve a **Ajustes** → **Dispositivos y servicios**.
2. Haz clic en **+ Añadir integración**.
3. Busca "**Investing Portfolio**".
4. Introduce tu **email y contraseña** de Investing.com.
5. **Selecciona un portfolio** de la lista.

> [!TIP]
> Si te registraste con Google, usa "Olvidé mi contraseña" en Investing.com para crear una contraseña. Puedes seguir usando Google en la app móvil.





## 📊 Entidades Creadas

Para un portfolio llamado "César", se crean estas entidades:

| Entidad                              | Descripción                                        | Unidad |
| ------------------------------------ | -------------------------------------------------- | ------ |
| `sensor.investing_cesar`             | **Capital invertido**: Valor total de mercado      | EUR    |
| `sensor.investing_cesar_openpl`      | **Open PL**: Ganancia/pérdida total acumulada      | EUR    |
| `sensor.investing_cesar_openplperc`  | **Open PL %**: Retorno de la inversión (ROI) total | %      |
| `sensor.investing_cesar_dailypl`     | **Daily PL**: Resultado de la sesión actual        | EUR    |
| `sensor.investing_cesar_dailyplperc` | **Daily PL %**: Cambio respecto al cierre anterior | %      |
| `button.update_investing_cesar`      | **Actualización manual**: Forzar refresco de datos | -      |

## ⏰ Horario de Actualizaciones

Puedes configurar los horarios de actualización en **Ajustes → Integraciones → Investing Portfolio → Configurar**:

| Opción                 | Predeterminado | Descripción                           |
| ---------------------- | -------------- | ------------------------------------- |
| Intervalo Lun-Vie      | 15 min         | Frecuencia durante horario de mercado |
| Hora inicio            | 9              | Hora de inicio del mercado            |
| Hora fin               | 21             | Hora de fin del mercado               |
| Actualización nocturna | 22:05          | Actualización al cierre               |
| Actualización mañana   | 04:00          | Actualización de madrugada            |

## 🐛 Solución de Problemas

### Error de autenticación
Verifica tu email y contraseña. Si usas login con Google, restablece tu contraseña en la web para obtener credenciales de email/contraseña. Puedes seguir usando tu cuenta de Google/Facebook normalmente para entrar en la app, pero ahora tendrás credenciales de email/contraseña al menos para esta integración.

### No aparecen portfolios
Solo se muestran carteras con posiciones (`portfolioType: position`). Las listas de seguimiento (watchlists) están excluidas.

### Los datos no se actualizan
La integración solo actualiza en horarios específicos. Usa el botón de actualización manual o revisa las opciones de horario.

## ⚖️ Licencia

MIT License
