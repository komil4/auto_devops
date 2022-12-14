# frozen_string_literal: true

# This file is managed by gitlab-ctl. Manual changes will be
# erased! To change the contents below, edit /etc/gitlab/gitlab.rb
# and run `sudo gitlab-ctl reconfigure`.

# Load "path" as a rackup file.
#
# The default is "config.ru".
#
environment 'production'
rackup '/opt/gitlab/embedded/service/gitlab-rails/config.ru'
pidfile '/opt/gitlab/var/puma/puma.pid'
state_path '/opt/gitlab/var/puma/puma.state'

stdout_redirect '/var/log/gitlab/puma/puma_stdout.log', '/var/log/gitlab/puma/puma_stderr.log', true

# Configure "min" to be the minimum number of threads to use to answer
# requests and "max" the maximum.
#
# The default is "0, 16".
#
threads 4, 4

# By default, workers accept all requests and queue them to pass to handlers.
# When false, workers accept the number of simultaneous requests configured.
#
# Queueing requests generally improves performance, but can cause deadlocks if
# the app is waiting on a request to itself. See https://github.com/puma/puma/issues/612
#
# When set to false this may require a reverse proxy to handle slow clients and
# queue requests before they reach puma. This is due to disabling HTTP keepalive
queue_requests false

# Bind the server to "url". "tcp://", "unix://" and "ssl://" are the only
# accepted protocols.
bind 'unix:///var/opt/gitlab/gitlab-rails/sockets/gitlab.socket'

bind 'tcp://127.0.0.1:8080'


directory '/var/opt/gitlab/gitlab-rails/working'

workers 2

require_relative "/opt/gitlab/embedded/service/gitlab-rails/lib/gitlab/cluster/lifecycle_events"
require_relative "/opt/gitlab/embedded/service/gitlab-rails/lib/gitlab/cluster/puma_worker_killer_initializer"

on_restart do
  # Signal application hooks that we're about to restart
  Gitlab::Cluster::LifecycleEvents.do_before_master_restart
end

options = { workers: 2 }

before_fork do
  enable_puma_worker_killer = !Gitlab::Utils.to_boolean(ENV['DISABLE_PUMA_WORKER_KILLER'])

  if enable_puma_worker_killer
    args = {}
    args[:puma_per_worker_max_memory_mb] = ENV['PUMA_WORKER_MAX_MEMORY'].to_i if ENV['PUMA_WORKER_MAX_MEMORY']
    Gitlab::Cluster::PumaWorkerKillerInitializer.start(options, **args)
  end

  # Signal application hooks that we're about to fork
  Gitlab::Cluster::LifecycleEvents.do_before_fork
end

Gitlab::Cluster::LifecycleEvents.set_puma_options options
on_worker_boot do
  # Signal application hooks of worker start
  Gitlab::Cluster::LifecycleEvents.do_worker_start
end

on_worker_shutdown do
  # Signal application hooks that a worker is shutting down
  Gitlab::Cluster::LifecycleEvents.do_worker_stop
end

# Preload the application before starting the workers; this conflicts with
# phased restart feature. (off by default)

preload_app!

tag 'gitlab-puma-worker'

# Verifies that all workers have checked in to the master process within
# the given timeout. If not the worker process will be restarted. Default
# value is 60 seconds.
#
worker_timeout 60

# https://github.com/puma/puma/blob/master/5.0-Upgrade.md#lower-latency-better-throughput
wait_for_less_busy_worker ENV.fetch('PUMA_WAIT_FOR_LESS_BUSY_WORKER', 0.001).to_f

# https://github.com/puma/puma/blob/master/5.0-Upgrade.md#nakayoshi_fork
nakayoshi_fork unless ENV['DISABLE_PUMA_NAKAYOSHI_FORK'] == 'true'

# Use customised JSON formatter for Puma log
require_relative "/opt/gitlab/embedded/service/gitlab-rails/lib/gitlab/puma_logging/json_formatter"

json_formatter = Gitlab::PumaLogging::JSONFormatter.new
log_formatter do |str|
    json_formatter.call(str)
end

lowlevel_error_handler do |ex, env|
  if Raven.configuration.capture_allowed?
    Raven.capture_exception(ex, tags: { 'handler': 'puma_low_level' }, extra: { puma_env: env })
  end

  # note the below is just a Rack response
  [500, {}, ["An error has occurred and reported in the system's low-level error handler."]]
end
