use csv::WriterBuilder;
use pdf_oxide::pipeline::converters::MarkdownOutputConverter;
use pdf_oxide::pipeline::{TextPipeline, TextPipelineConfig};
use pdf_oxide::PdfDocument;
use pulldown_cmark::{Event, HeadingLevel, Parser, Tag, TagEnd};
use std::error::Error;
use std::fs;

fn main() -> Result<(), Box<dyn Error>> {
    println!("Extracting PDF to Markdown with layout preservation...");
    
    // 1. Open the PDF
    let mut doc = PdfDocument::open("input.pdf")?;
    let mut full_markdown = String::new();

    // 2. Setup the Advanced Text Pipeline
    let config = TextPipelineConfig::default();
    let pipeline = TextPipeline::with_config(config.clone());
    let converter = MarkdownOutputConverter::new();

    // 3. Extract text page-by-page and accumulate into one large Markdown string
    for page_num in 0..doc.page_count() {
        // Extract raw spans
        let spans = doc.extract_spans(page_num)?;
        
        // Reorder spans based on visual layout (fixes multi-column PDFs)
        let ordered_spans = pipeline.process(spans, Default::default())?;
        
        // Convert page layout into Markdown
        let page_md = converter.convert(&ordered_spans, &config)?;
        
        full_markdown.push_str(&page_md);
        full_markdown.push_str("\n\n");
    }

    println!("Markdown extracted! Converting to TSV format...");

    // 4. Parse the accumulated Markdown into the TSV structure
    let tsv_output = markdown_to_tsv(&full_markdown, b'\t')?;
    
    // 5. Save the output
    fs::write("output.tsv", tsv_output)?;
    
    println!("Successfully saved hierarchical data to output.tsv!");

    Ok(())
}

/// Parses a Markdown string and outputs TSV with hierarchical headings mapped to columns.
fn markdown_to_tsv(markdown: &str, delimiter: u8) -> Result<String, Box<dyn Error>> {
    // Track 6 standard Markdown heading levels (H1 to H6)
    let mut headings = vec![String::new(); 6];
    let mut current_text = String::new();
    
    // Create an in-memory TSV writer
    let mut wtr = WriterBuilder::new()
        .delimiter(delimiter)
        .from_writer(vec![]);
    
    // Write the TSV header row
    wtr.write_record(&[
        "heading0", "heading1", "heading2", 
        "heading3", "heading4", "heading5", "Text"
    ])?;

    // Iterate through Markdown events
    for event in Parser::new(markdown) {
        match event {
            // --- HEADINGS ---
            Event::Start(Tag::Heading { .. }) => {
                // Flush any dangling text right before a heading
                flush_text(&mut wtr, &headings, &mut current_text)?;
            }
            Event::End(TagEnd::Heading(level)) => {
                let depth = level_to_usize(level) - 1;
                
                // Save the new heading text
                headings[depth] = current_text.trim().to_string();
                
                // CRITICAL: Reset any smaller sub-headings 
                // e.g., if we hit a new H1 (heading0), erase old H2, H3, etc.
                for h in headings.iter_mut().skip(depth + 1) {
                    h.clear();
                }
                
                current_text.clear();
            }

            // --- BLOCK ELEMENTS (Paragraphs, Lists, BlockQuotes) ---
            Event::Start(Tag::Paragraph) 
            | Event::Start(Tag::Item) 
            | Event::Start(Tag::CodeBlock(_))
            | Event::Start(Tag::BlockQuote)
            | Event::Start(Tag::TableRow) => {
                flush_text(&mut wtr, &headings, &mut current_text)?;
            }
            
            Event::End(TagEnd::Paragraph) 
            | Event::End(TagEnd::Item) 
            | Event::End(TagEnd::CodeBlock)
            | Event::End(TagEnd::BlockQuote)
            | Event::End(TagEnd::TableRow) => {
                // Write out the collected text block as a new TSV row
                flush_text(&mut wtr, &headings, &mut current_text)?;
            }

            // --- TABLES (Join cells with a pipe separator for single-cell display) ---
            Event::End(TagEnd::TableCell) => {
                current_text.push_str(" | ");
            }

            // --- INLINE TEXT ACCUMULATION ---
            Event::Text(t) | Event::Code(t) | Event::Html(t) | Event::InlineHtml(t) => {
                current_text.push_str(&t);
            }
            Event::SoftBreak | Event::HardBreak => {
                // Replace line breaks inside a paragraph with a space so it stays on one TSV line
                current_text.push(' '); 
            }
            _ => {}
        }
    }

    // Flush any remaining trailing text at the end of the document
    flush_text(&mut wtr, &headings, &mut current_text)?;

    wtr.flush()?;
    let result = String::from_utf8(wtr.into_inner()?)?;
    Ok(result)
}

/// Helper function to output the record and empty the text buffer
fn flush_text(
    wtr: &mut csv::Writer<Vec<u8>>,
    headings: &[String],
    current_text: &mut String,
) -> Result<(), Box<dyn Error>> {
    let mut text = current_text.trim();
    
    // Clean up trailing table separators if a table was processed
    if text.ends_with(" |") {
        text = text[..text.len() - 2].trim();
    }

    // Only write a row if there is actual text content
    if !text.is_empty() {
        wtr.write_record(&[
            &headings[0], &headings[1], &headings[2],
            &headings[3], &headings[4], &headings[5],
            text
        ])?;
    }
    
    // Clear the buffer to start collecting the next block
    current_text.clear();
    Ok(())
}

/// Maps the Heading enum to an array index (1 to 6)
fn level_to_usize(level: HeadingLevel) -> usize {
    match level {
        HeadingLevel::H1 => 1,
        HeadingLevel::H2 => 2,
        HeadingLevel::H3 => 3,
        HeadingLevel::H4 => 4,
        HeadingLevel::H5 => 5,
        HeadingLevel::H6 => 6,
    }
}
