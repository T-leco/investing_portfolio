<p align="center">
<picture>
  <img alt="Investing Portfolio Logo" src="./logos/logo@2x.png" width="400">
</picture>
</p>

<p align="center">
<img src="https://img.shields.io/badge/HACS-Custom-orange.svg">
<img src="https://img.shields.io/maintenance/yes/2025.svg">
<img src="https://img.shields.io/badge/version-1.0.0-blue">
<a href="https://github.com/T-leco/investing_portfolio/issues"><img alt="Issues" src="https://img.shields.io/github/issues/T-leco/investing_portfolio?color=0088ff"></a>
<a href="https://www.buymeacoffee.com/teleco"><img alt="Buy Me A Coffee" src="https://img.shields.io/badge/support-buymeacoffee?logo=buymeacoffee&logoColor=black&color=%23FFDD00"></a>
</p>

<p align="center" style="font-weight:bold">
  🚀 Track your investments directly in Home Assistant.
</p>

<p align="center">
  <a href="#features">✨ Features</a> ·
  <a href="#installation">⬇️ Installation</a> ·
  <a href="#entities-created">📊 Entities</a> ·
  <a href="#troubleshooting">🐛 Troubleshooting</a>
</p>

<br>

Take full control of your financial data by integrating your [Investing.com](https://www.investing.com/) portfolios into your smart home. This integration provides real-time-like tracking of your stocks, crypto, and funds, allowing you to create powerful automations and stunning dashboards based on your net worth and daily performance.

> [!IMPORTANT]
> This integration uses the **official Investing.com API endpoint** used by their mobile app. **No web scraping** is involved, ensuring higher reliability and performance.


## ✨ Features

- **Multiple Portfolios support**: Add multiple portfolios as separate entries.
- **Dynamic Entities**: Entities use the portfolio name (e.g., `sensor.investing_cesar`).
- **Device Registry**: All entities are grouped under an "Investing {Portfolio}" device in the UI.
- **Comprehensive Sensors**: Invested capital, total change, daily change, percentages.
- **Manual Update**: Button to force refresh data for each portfolio.
- **Configurable Updates**: Set update schedules via options.
- **Error Notifications**: Receive alerts for expired tokens or issues.
- **Optimized for Home Assistant**: Uses HA's shared session pool for efficiency.

## ✅ Prerequisites

- Home Assistant installed (2023.8.0 or newer).
- [HACS](https://hacs.xyz/) installed (for the recommended installation method).
- An [Investing.com](https://www.investing.com/) account.

## Installation

Easiest install is via [HACS](https://hacs.xyz/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=T-leco&repository=investing_portfolio&category=integration)

`HACS -> Integrations -> Explore & Add Repositories -> Investing Portfolio`

> [!NOTE]
> HACS does not "configure" the integration for you. After installing via HACS, go to **Settings → Devices & Services → Add Integration** and search for "Investing Portfolio".

For manual installation, copy `custom_components/investing_portfolio` to your `custom_components` folder in Home Assistant.

### Configuration

1. Go to **Settings** → **Devices & Services**.
2. Click **+ Add Integration**.
3. Search for "**Investing Portfolio**".
4. Enter your Investing.com **email and password**.
5. **Select a portfolio** from the list.

> [!TIP]
> If you signed up with Google, use the "Forgot Password" feature on Investing.com to set a password. You can still use Google login in the mobile app.




## 📊 Entities Created

For a portfolio named "Cesar", the following entities are created:

| Entity                               | Description                                          | Unit |
| ------------------------------------ | ---------------------------------------------------- | ---- |
| `sensor.investing_cesar`             | **Invested Capital**: Total market value of holdings | EUR  |
| `sensor.investing_cesar_openpl`      | **Open PL**: Total profit/loss since opening         | EUR  |
| `sensor.investing_cesar_openplperc`  | **Open PL %**: Total ROI percentage                  | %    |
| `sensor.investing_cesar_dailypl`     | **Daily PL**: Profit/loss for current session        | EUR  |
| `sensor.investing_cesar_dailyplperc` | **Daily PL %**: Change vs previous close             | %    |
| `button.update_investing_cesar`      | **Manual Update**: Force data refresh                | -    |


## ⏰ Update Schedule

You can configure update times via **Settings → Integrations → Investing Portfolio → Configure**:

| Option           | Default | Description                    |
| ---------------- | ------- | ------------------------------ |
| Mon-Fri Interval | 15 min  | Frequency during trading hours |
| Start Hour       | 9       | Trading start hour             |
| End Hour         | 21      | Trading end hour               |
| Night Update     | 22:05   | Update at market close         |
| Morning Update   | 04:00   | Early morning update           |

## 🐛 Troubleshooting

### Authentication Error
Verify your email and password. If using Google login, reset your password in the web to get email/password credentials. You can still use your Google/Facebook account normally to login to the app but now you will have email/password credentials at least for this integration.

### Portfolios not showing
Only portfolios containing positions (`portfolioType: position`) are shown. Watchlists are excluded.

### Data not updating
The integration only updates during scheduled times. Use the manual update button or check schedule options.

## ⚖️ License

MIT License
