"""Renderizador paralelo: cada worker dibuja frames y los guarda como PNG."""
import os, sys, time
import multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _work(args):
    idxs, W, H, outdir = args
    import scenes
    from engine import png_write
    t0 = time.time()
    for i in idxs:
        img = scenes.build_frame(i, W, H)
        png_write(os.path.join(outdir, 'f%05d.png' % i), img)
    return (len(idxs), time.time() - t0)


def main():
    W = int(sys.argv[1]); H = int(sys.argv[2])
    outdir = sys.argv[3]
    nproc = int(sys.argv[4]) if len(sys.argv) > 4 else max(1, mp.cpu_count() - 2)
    lo = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    hi = int(sys.argv[6]) if len(sys.argv) > 6 else None
    import scenes
    hi = scenes.NF if hi is None else hi
    os.makedirs(outdir, exist_ok=True)
    idxs = [i for i in range(lo, hi) if not os.path.exists(os.path.join(outdir, 'f%05d.png' % i))]
    print('frames a renderizar:', len(idxs), 'procesos:', nproc, flush=True)
    chunks = [idxs[k::nproc] for k in range(nproc)]
    chunks = [c for c in chunks if c]
    t0 = time.time()
    with mp.Pool(len(chunks)) as p:
        res = p.map(_work, [(c, W, H, outdir) for c in chunks])
    tot = sum(r[0] for r in res)
    print('hechos', tot, 'frames en', round(time.time() - t0, 1), 's', flush=True)


if __name__ == '__main__':
    main()
