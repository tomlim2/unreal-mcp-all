import SectionPageClient from "./SectionPageClient";

export default async function SectionPage({
  params,
}: {
  params: Promise<{ 'section-id': string }>;
}) {
  const resolvedParams = await params;
  return <SectionPageClient sectionId={resolvedParams['section-id']} />;
}

// For static export, declare that there are no pre-rendered params.
export function generateStaticParams() {
  return [] as { 'section-id': string }[];
}