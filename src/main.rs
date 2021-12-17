#[macro_use]
extern crate clap;

use std::error::Error;
pub type Result<T> = std::result::Result<T,Box<dyn Error>>;

pub mod cli;
use cli::cli;

pub mod scraper;
pub mod files;
pub mod config;

#[tokio::main]
async fn main() -> Result<()>{
    cli().await?;

    Ok(())
}