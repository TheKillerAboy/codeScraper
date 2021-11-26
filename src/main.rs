mod codeforces;
use error_chain::error_chain;
use std::path::Path;
use futures::{executor, future};

error_chain! {
    foreign_links {
        Io(std::io::Error);
        HttpRequest(reqwest::Error);
        Codeforces(codeforces::Error);
    }
}

#[tokio::main]
async fn main() -> Result<()>{
    let contest_id = 1611;
    let problems = codeforces::list_contest_problems(contest_id).await?;
    let dir = Path::new("/Users/annekin.meyburgh/workspace/codeScraper/tmp");
    let futures = problems.iter().map(|problem| codeforces::write_io(&dir, contest_id, &problem));

    let _results = future::join_all(futures).await;
    Ok(())
}
