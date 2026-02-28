// PM2 ecosystem config for Brain services.
// Adjust paths to match your installation.

const HOME = process.env.HOME || '/root';
const BRAIN_DIR = `${HOME}/brain`;

module.exports = {
  apps: [{
    name: 'brain-monitor',
    script: 'scripts/monitor.py',
    interpreter: `${HOME}/.local/bin/uv`,
    interpreter_args: `run --directory ${BRAIN_DIR} python`,
    cwd: BRAIN_DIR,
    restart_delay: 10000,
    max_restarts: 10,
    autorestart: true,
  }, {
    name: 'brain-whisper',
    script: 'src/brain/whisper_server.py',
    interpreter: `${HOME}/.local/bin/uv`,
    interpreter_args: `run --directory ${BRAIN_DIR} python`,
    cwd: BRAIN_DIR,
    restart_delay: 5000,
    max_restarts: 5,
    autorestart: true,
  }]
};
