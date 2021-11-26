use scraper::Html;
use scraper::Selector;
use regex::Regex;
use std::fs;
use tokio::time::{sleep, Duration};

use error_chain::error_chain;
error_chain! {
    foreign_links {
        Io(std::io::Error);
        HttpRequest(reqwest::Error);
    }
}

pub fn get_contest(contest_id: i32) {
}

pub struct CFProblemDetails{
    pub letter: String,
    pub name: String,
}

pub async fn list_contest_problems(contest_id: i32) -> Result<Vec<CFProblemDetails>> {
    let page_url = format!("https://codeforces.com/contest/{}", contest_id);
    println!("Page URL: {}", page_url);
    let res = reqwest::get(page_url).await?;
    let body = res.text().await?;
    let parsed_html = Html::parse_document(&body);
    let selector = Selector::parse("table.problems tr").unwrap();
    let column_selector = Selector::parse("td a").unwrap();
    let re_name_searcher = Regex::new("-->(.*)<!--").unwrap();

    let mut output:Vec<CFProblemDetails> = Vec::new();
    for problem_field in parsed_html.select(&selector) {
        let letter_html = problem_field.select(&column_selector).nth(0);
        if ! letter_html.is_none() {
            let letter = letter_html.unwrap().inner_html().trim().to_string();
            let mut name = problem_field.select(&column_selector).nth(1).unwrap().inner_html();
            name = re_name_searcher.captures(&name).unwrap().get(1).unwrap().as_str().trim().to_string();

            output.push(CFProblemDetails{letter, name});
        }
    }
    Ok(output)
}

pub fn get_io_file_name(problem: &CFProblemDetails, ext: &str, i: usize) -> String{
    let name = problem.name.replace(" ","-");
    return format!("{}-{}.{}.{}", problem.letter.to_lowercase(), name.to_lowercase(), ext, i);
}

pub async fn write_io(directory: &std::path::Path,contest_id: i32, problem: &CFProblemDetails) -> Result<()>{
    println!("Getting Problem {}. {}", problem.letter, problem.name);
    let page_url = format!("https://codeforces.com/contest/{}/problem/{}", contest_id, problem.letter);
    let res = reqwest::get(page_url).await?;
    let body = res.text().await?;
    let parsed_html = Html::parse_document(&body);
    sleep(Duration::from_millis(50)).await;

    let input_selector = Selector::parse(".input pre").unwrap();
    for (i, input_html) in parsed_html.select(&input_selector).enumerate() {
        let input_data =input_html.inner_html().trim().to_string();
        let file_name = directory.join(get_io_file_name(problem, "in", i));
        println!("Writing file {}", file_name.to_str().unwrap());
        fs::write(file_name, input_data)?;
        sleep(Duration::from_millis(50)).await;
    }

    let output_selector = Selector::parse(".output pre").unwrap();
    let output_data = parsed_html.select(&output_selector).next().unwrap().inner_html().trim().to_string();
    for (i, output_html) in parsed_html.select(&output_selector).enumerate() {
        let output_data =output_html.inner_html().trim().to_string();
        let file_name = directory.join(get_io_file_name(problem, "out", i));
        println!("Writing file {}", file_name.to_str().unwrap());
        fs::write(file_name, output_data)?;
        sleep(Duration::from_millis(50)).await;
    }

    Ok(())
}