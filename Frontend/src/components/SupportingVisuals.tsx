import { API_BASE_URL } from "@/lib/api";

type Visual = {
  path: string;
  page: number;
};

export default function SupportingVisuals({
  visuals,
}: {
  visuals: Visual[];
}) {
  if (!visuals || visuals.length === 0) return null;

  return (
    <div className="mt-6">
      <h3 className="font-semibold text-lg mb-3">
        Supporting Visuals
      </h3>

      <div className="space-y-4">
        {visuals.map((v, i) => (
          <div
            key={i}
            className="border rounded-xl p-2 shadow-sm"
          >
            <p className="text-sm text-gray-500 mb-2">
              Page {v.page}
            </p>

            <img
              src={`${API_BASE_URL}/${v.path.replace(/^\//, "")}`}
              alt={`Visual from page ${v.page}`}
              className="rounded-xl w-full"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
