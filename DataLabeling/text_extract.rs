use pdf_oxide::PdfDocument;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut doc = PdfDocument::open("report.pdf")?;
    
    // Convert the first page to Markdown, keeping headings and layout
    let markdown = doc.to_markdown(0, Default::default())?;
    println!("{}", markdown);
    
    Ok(())
}