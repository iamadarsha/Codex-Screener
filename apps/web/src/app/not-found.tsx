import Link from "next/link";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-page px-6 text-center text-white">
      <div className="text-xs uppercase tracking-[0.22em] text-[#5C5D6E]">
        404
      </div>
      <h1 className="text-3xl font-bold">Page not found</h1>
      <Link
        href="/"
        className="inline-flex h-10 items-center justify-center rounded-lg border border-accent px-4 text-sm font-semibold text-accent"
      >
        Return home
      </Link>
    </div>
  );
}
