"use client";
import DocumentsPage from "@/components/DocumentsPage";

export default function PersonalDetailsPage() {
  return (
    <DocumentsPage
      category="personal_details"
      current="Personal Details"
      title="Student Personal"
      accent="Details"
      hint="Download each student's record from the CAMPS portal (Student › Reports › Student Record, or Student Detail View) and upload it here."
      defaultTitle="CAMPS Student Record"
    />
  );
}
