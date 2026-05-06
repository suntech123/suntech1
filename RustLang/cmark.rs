use pulldown_cmark::{Event, Parser, Tag, TagEnd, HeadingLevel};

fn main() {
    // Imagine this is the markdown string you extracted from your output.json
    let markdown_text = "
# Plan Document and Summary Plan Description
Copyright © 2025 Oracle Confidential.

## UnitedHealthcare - PPO Medical Plan
This section contains **important** information about your *dental* and medical coverage.

### DENTAL BENEFITS
Please refer to the table below.
    ";

    println!("Scanning Markdown for structure...\n");

    // Initialize the parser
    let parser = Parser::new(markdown_text);

    // State variables to keep track of where we are in the document
    let mut current_heading_level: Option<HeadingLevel> = None;
    let mut in_bold = false;
    let mut in_italic = false;

    // Iterate through the stream of Markdown events
    for event in parser {
        match event {
            // --- DETECT HEADINGS ---
            Event::Start(Tag::Heading { level, .. }) => {
                current_heading_level = Some(level);
            }
            Event::End(TagEnd::Heading(_)) => {
                current_heading_level = None;
            }

            // --- DETECT BOLD TEXT ---
            Event::Start(Tag::Strong) => {
                in_bold = true;
            }
            Event::End(TagEnd::Strong) => {
                in_bold = false;
            }

            // --- DETECT ITALIC TEXT ---
            Event::Start(Tag::Emphasis) => {
                in_italic = true;
            }
            Event::End(TagEnd::Emphasis) => {
                in_italic = false;
            }

            // --- EXTRACT THE ACTUAL TEXT ---
            Event::Text(text) => {
                // If we are currently inside a heading, print it out
                if let Some(level) = current_heading_level {
                    // level is an enum (H1, H2, H3, etc.)
                    println!("[FOUND HEADING {:?}] -> {}", level, text);
                } 
                // If we are inside bold text
                else if in_bold {
                    println!("[FOUND BOLD TEXT] -> {}", text);
                } 
                // If we are inside italic text
                else if in_italic {
                    println!("[FOUND ITALIC TEXT] -> {}", text);
                }
            }
            
            // Ignore other events (like newlines, lists, paragraphs starting/ending)
            _ => {}
        }
    }
}