import React from 'react';

export const HowItWorks: React.FC = () => {

  return (
    <section className="py-16 sm:py-20 lg:py-24 border-b border-[#E2E3DC] bg-canvas">
      <div className="mx-auto max-w-[1248px] px-4 sm:px-6 lg:px-8">
        {/* Section Heading matching Screenshot (545).png and framer.md */}
        <div className="mb-12 sm:mb-16 max-w-4xl">
          <h2 className="font-sans text-[36px] sm:text-[46px] lg:text-[54px] font-extrabold text-[#000000] tracking-[-0.035em] leading-[1.04]">
            From raw series to checked features
          </h2>
        </div>

        {/* 4 Cards Workflow Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: Connect read-only / Zero-copy */}
          <div className="flex flex-col gap-5 group">
            {/* Visual Box Art */}
            <div className="rounded-xl border border-[#D8D9D2] bg-white p-4 h-[168px] flex flex-col justify-between shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-200 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
              <div className="space-y-2.5">
                <div className="flex items-center gap-3 text-[13px]">
                  <span className="text-[#6B6D65] w-14 font-sans">Buffer</span>
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded-[4px] bg-[#F2F3EF] text-[#000000] font-medium border border-[#E2E3DC]">
                    numpy.ndarray
                  </span>
                </div>

                <div className="flex items-center gap-3 text-[13px]">
                  <span className="text-[#6B6D65] w-14 font-sans">Memory</span>
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded-[4px] bg-[#F2F3EF] text-[#000000] font-medium border border-[#E2E3DC]">
                    zero-copy FFI
                  </span>
                  <span className="ml-auto flex items-center gap-1 text-[11px] text-[#6B6D65]">
                    <svg className="w-3 h-3 text-[#6B6D65]" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <rect x="3" y="7" width="10" height="7" rx="1.5" />
                      <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" />
                    </svg>
                    <span>Read-only</span>
                  </span>
                </div>
              </div>

              {/* Status Note */}
              <div className="pt-2.5 border-t border-[#E2E3DC] flex items-center gap-2 text-[12px] text-[#000000]">
                <span className="flex h-3.5 w-3.5 items-center justify-center rounded-[3px] bg-[#000000] text-white flex-none">
                  <svg className="h-2 w-2 stroke-white" viewBox="0 0 12 12" fill="none" strokeWidth="2.5">
                    <path d="M2.5 6.5L5 9L9.5 3.5" />
                  </svg>
                </span>
                <span className="font-sans font-medium text-[12px]">
                  Schema mapped. Rows stay put.
                </span>
              </div>
            </div>

            {/* Step Text */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2.5">
                <span className="flex h-5 w-5 items-center justify-center rounded-[4px] border border-[#D8D9D2] bg-white font-sans text-[11px] font-bold text-[#000000] shadow-sm">
                  1
                </span>
                <h3 className="font-sans text-[16px] font-bold text-[#000000] tracking-tight">
                  Connect read-only
                </h3>
              </div>
              <p className="font-sans text-[13.5px] text-[#50524B] leading-[1.45]">
                Point Kymora at NumPy buffers, Polars Series, or Arrow memory with zero-copy views. No serialization or IPC overhead.
              </p>
            </div>
          </div>

          {/* Card 2: Ask like you'd ask a colleague */}
          <div className="flex flex-col gap-5 group">
            {/* Visual Box Art */}
            <div className="rounded-xl border border-[#D8D9D2] bg-white p-4 h-[168px] flex flex-col justify-between shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-200 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
              <div className="rounded-lg border border-[#D8D9D2] bg-[#F2F3EF]/50 p-2.5">
                <p className="text-[12.5px] font-medium text-[#000000] leading-snug font-sans">
                  Extract 33 features across 100k series, parallel=Rayon
                  <span className="inline-block w-0.5 h-3.5 bg-[#000000] ml-0.5 animate-pulse align-middle" />
                </p>
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="font-sans text-[12px] text-[#6B6D65]">
                  Plain Python
                </span>
                <span className="px-3.5 py-1 text-xs font-semibold rounded-md bg-[#000000] text-white shadow-sm hover:bg-neutral-800 transition">
                  Extract
                </span>
              </div>
            </div>

            {/* Step Text */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2.5">
                <span className="flex h-5 w-5 items-center justify-center rounded-[4px] border border-[#D8D9D2] bg-white font-sans text-[11px] font-bold text-[#000000] shadow-sm">
                  2
                </span>
                <h3 className="font-sans text-[16px] font-bold text-[#000000] tracking-tight">
                  Ask like you’d ask a colleague
                </h3>
              </div>
              <p className="font-sans text-[13.5px] text-[#50524B] leading-[1.45]">
                Call extraction in plain Python. You don’t need complicated feature pipelines or manual C extensions first.
              </p>
            </div>
          </div>

          {/* Card 3: It writes, runs, and checks the query */}
          <div className="flex flex-col gap-5 group">
            {/* Visual Box Art */}
            <div className="rounded-xl border border-[#D8D9D2] bg-white p-4 h-[168px] flex flex-col justify-between shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-200 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)]">
              <div className="font-mono text-[11px] leading-[1.65] text-[#000000] overflow-hidden">
                <div className="truncate">
                  <span className="text-[#C93B2B] font-medium">features</span> = km.<span className="text-[#1A56DB] font-medium">extract_features</span>(
                </div>
                <div className="truncate pl-3">
                  buffer, features=[<span className="text-[#1E7E34]">'hurst'</span>, <span className="text-[#1E7E34]">'sample_entropy'</span>],
                </div>
                <div className="truncate pl-3">
                  n_jobs=-<span className="text-[#1A56DB]">1</span>
                </div>
                <div className="truncate text-[#6B6D65]">
                  ) -- Rayon SIMD threadpool dispatch
                </div>
              </div>

              {/* Status Note */}
              <div className="pt-2 border-t border-[#E2E3DC] flex items-center gap-2 text-[12px] text-[#000000]">
                <span className="flex h-3.5 w-3.5 items-center justify-center rounded-[3px] bg-[#000000] text-white flex-none">
                  <svg className="h-2 w-2 stroke-white" viewBox="0 0 12 12" fill="none" strokeWidth="2.5">
                    <path d="M2.5 6.5L5 9L9.5 3.5" />
                  </svg>
                </span>
                <span className="font-sans font-medium text-[12px]">
                  Checked before it answers
                </span>
              </div>
            </div>

            {/* Step Text */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2.5">
                <span className="flex h-5 w-5 items-center justify-center rounded-[4px] border border-[#D8D9D2] bg-white font-sans text-[11px] font-bold text-[#000000] shadow-sm">
                  3
                </span>
                <h3 className="font-sans text-[16px] font-bold text-[#000000] tracking-tight">
                  It compiles, runs, and checks the extractors
                </h3>
              </div>
              <p className="font-sans text-[13.5px] text-[#50524B] leading-[1.45]">
                The Rust engine releases the GIL, runs vectorized SIMD kernels across Rayon threads, and validates IEEE-754 bounds.
              </p>
            </div>
          </div>

          {/* Card 4: You check the work */}
          <div className="flex flex-col gap-5 group">
            {/* Visual Box Art */}
            <div className="rounded-xl border border-[#D8D9D2] bg-white p-3.5 h-[168px] flex flex-col justify-between shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-all duration-200 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)] overflow-hidden">
              <div className="w-full font-sans text-[12px] tabular-nums">
                {/* Table Header */}
                <div className="grid grid-cols-3 text-[#6B6D65] pb-1 border-b border-[#E2E3DC] text-[11px] font-medium">
                  <span>Series ID</span>
                  <span className="text-right">Samp_Ent</span>
                  <span className="text-right">Hurst</span>
                </div>

                {/* Row 1 */}
                <div className="grid grid-cols-3 py-1 border-b border-[#E2E3DC]/60 text-[#000000]">
                  <span className="font-mono text-[11px]">TS-0947</span>
                  <span className="text-right font-mono text-[11px]">0.412</span>
                  <span className="text-right font-mono text-[11px]">0.89</span>
                </div>

                {/* Row 2 (AUTHENTIC HIGHLIGHT ROW WITH #FFE53B!) */}
                <div className="grid grid-cols-3 py-1 bg-[#FFE53B] -mx-3.5 px-3.5 font-bold text-[#000000]">
                  <span className="font-mono text-[11px]">TS-1182</span>
                  <span className="text-right font-mono text-[11px]">0.384</span>
                  <span className="text-right font-mono text-[11px]">0.92</span>
                </div>

                {/* Row 3 */}
                <div className="grid grid-cols-3 py-1 text-[#000000]">
                  <span className="font-mono text-[11px]">TS-1310</span>
                  <span className="text-right font-mono text-[11px]">0.395</span>
                  <span className="text-right font-mono text-[11px]">0.87</span>
                </div>
              </div>

              {/* Table Footer */}
              <div className="pt-1.5 border-t border-[#E2E3DC] flex items-center justify-between text-[11px] text-[#6B6D65]">
                <span>Rows behind the feature</span>
                <span className="underline font-semibold text-[#000000] cursor-pointer hover:text-neutral-700">
                  Open
                </span>
              </div>
            </div>

            {/* Step Text */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2.5">
                <span className="flex h-5 w-5 items-center justify-center rounded-[4px] border border-[#D8D9D2] bg-white font-sans text-[11px] font-bold text-[#000000] shadow-sm">
                  4
                </span>
                <h3 className="font-sans text-[16px] font-bold text-[#000000] tracking-tight">
                  You check the work
                </h3>
              </div>
              <p className="font-sans text-[13.5px] text-[#50524B] leading-[1.45]">
                Every feature links back to the exact time-series windows and raw sample buffers it was computed from. Click through to inspect.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
