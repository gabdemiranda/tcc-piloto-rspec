"""Isola código Ruby gerado em Linux. Falha se o isolamento estiver indisponível."""
import ctypes as C
import errno
import os
from pathlib import Path
import resource
import signal
import subprocess
import tempfile
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]

def run_ruby(args, work, candidate, seconds=30, coverage=False, extra_env=None):
    work, candidate = Path(work).resolve(), Path(candidate).resolve()
    work.mkdir(parents=True, exist_ok=True)
    # Só o arquivo do alvo é montado: a suíte não vê os outros métodos.
    source = (ROOT / (extra_env or {}).get("TCC_TARGET_SOURCE", "")).resolve()
    if source != ROOT and (source.parent != ROOT / "lib" or not source.is_file()):
        raise ValueError("Fonte deve ser um arquivo em lib/")
    runtime = os.environ.get("TCC_RUBY_ROOT")
    if runtime:
        runtime = Path(runtime).resolve()
        ruby = "/ruby-runtime/usr/bin/ruby3.3"
        paths = [
            ("LD_LIBRARY_PATH", "/ruby-runtime/usr/lib/x86_64-linux-gnu"),
            ("RUBYLIB", "/ruby-runtime/usr/lib/ruby/3.3.0:/ruby-runtime/usr/lib/x86_64-linux-gnu/ruby/3.3.0:/ruby-runtime/usr/lib/ruby/vendor_ruby"),
            ("GEM_PATH", "/gems:/ruby-runtime/usr/share/rubygems-integration/all:/ruby-runtime/usr/lib/ruby/gems/3.3.0"),
        ]
        binds = ["--ro-bind", str(runtime), "/ruby-runtime"]
    else:
        ruby = os.environ.get("TCC_RUBY_BIN", "/usr/bin/ruby")
        if not ruby.startswith("/usr/"):
            raise RuntimeError("Use Ruby instalado em /usr, ou configure TCC_RUBY_ROOT.")
        paths, binds = [("GEM_PATH", "/gems")], []
    gems = Path(os.environ["TCC_GEM_HOME"]).resolve()
    binds += ["--ro-bind", str(gems), "/gems"]
    sc = C.CDLL("libseccomp.so.2")
    sc.seccomp_init.argtypes, sc.seccomp_init.restype = [C.c_uint32], C.c_void_p
    sc.seccomp_rule_add.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_uint]
    sc.seccomp_syscall_resolve_name.argtypes = [C.c_char_p]
    sc.seccomp_export_bpf.argtypes = [C.c_void_p, C.c_int]
    sc.seccomp_release.argtypes = [C.c_void_p]
    ctx = sc.seccomp_init(0x7fff0000)
    if not ctx:
        raise RuntimeError("Não foi possível inicializar seccomp")
    with tempfile.TemporaryFile() as filt:
        try:
            for call in (b"socket", b"socketpair", b"ptrace", b"process_vm_writev", b"io_uring_setup"):
                num = sc.seccomp_syscall_resolve_name(call)
                if num < 0 or sc.seccomp_rule_add(ctx, 0x50000 | errno.EPERM, num, 0) != 0:
                    raise RuntimeError("Falha ao isolar syscall: " + call.decode())
            if sc.seccomp_export_bpf(ctx, filt.fileno()) != 0:
                raise RuntimeError("Falha ao exportar filtro seccomp")
        finally:
            sc.seccomp_release(ctx)
        filt.seek(0)
        env = [("PATH", "/usr/bin:/bin"), ("HOME", "/tmp"), ("LANG", "C.UTF-8"),
               ("TZ", "UTC"), ("GEM_HOME", "/gems"), *paths]
        if coverage:
            env += [("RUBYOPT", "-r/study/tools/coverage_helper.rb")]
        env += [(k,v) for k,v in (extra_env or {}).items() if k != "TCC_TARGET_SOURCE"]
        cmd = [
            "bwrap", "--unshare-user", "--unshare-pid", "--unshare-ipc", "--unshare-uts",
            "--die-with-parent", "--new-session", "--clearenv",
            "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib",
            "--symlink", "usr/lib64", "/lib64", "--symlink", "usr/bin", "/bin",
            "--proc", "/proc", "--dev", "/dev", "--size", "33554432", "--tmpfs", "/tmp",
            "--dir", "/study", "--dir", "/study/lib",
            *(["--ro-bind", str(source), "/study/lib/" + source.name] if source != ROOT
              else ["--ro-bind", str(ROOT / "lib"), "/study/lib"]),
            "--ro-bind", str(ROOT / "tools" / "coverage_helper.rb"), "/study/tools/coverage_helper.rb",
            "--ro-bind", str(ROOT / "tools" / "mutant_bridge.rb"), "/study/tools/mutant_bridge.rb",
            "--ro-bind", str(candidate), "/study/spec/candidate_spec.rb",
            "--bind", str(work), "/work", "--chdir", "/study", *binds,
            "--seccomp", str(filt.fileno()),
        ]
        for k,v in env:
            cmd += ["--setenv", k, v]
        cmd += ["--", ruby, *args]
        def limit():
            resource.setrlimit(resource.RLIMIT_CPU, (max(2,int(seconds)), max(2,int(seconds))+1))
            resource.setrlimit(resource.RLIMIT_FSIZE, (8*1024**2,8*1024**2))
            resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,768*1024**2))
        t = monotonic()
        with tempfile.TemporaryFile() as out:
            proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT,
                                    pass_fds=(filt.fileno(),), preexec_fn=limit,
                                    start_new_session=True)
            try:
                proc.wait(timeout=seconds)
                timeout = False
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                timeout = True
            out.seek(0)
            log = out.read(65536).decode("utf-8", errors="replace")
        if log.startswith("bwrap:"):
            raise RuntimeError(log.strip())
        return {"status": proc.returncode, "timeout": timeout, "seconds": monotonic()-t, "log": log}
