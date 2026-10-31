"use client";
import DocumentsPage from "@/components/DocumentsPage";

export default function MedicalLeavePage() {
  return (
    <DocumentsPage
      category="medical_leave"
      current="Medical Leave"
      title="Medical Leave"
      accent="Proof"
      hint="For every medical leave, upload the medical certificate or the parent's written letter explaining the health issue."
      defaultTitle="Medical Certificate"
      withDates
    />
  );
}
