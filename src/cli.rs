use crate::Result;
use clap::{App,ArgMatches};
use crate::scraper::{get_problems, get_problem_data};
use crate::files::write_file;
use crate::config;
use std::collections::HashMap;
use std::fs;
use glob::glob;

async fn get(matches: &ArgMatches<'_>) -> Result<()>{
    let contest_id = matches.value_of("CONTEST_ID").unwrap();
    let contest_id = contest_id.parse::<u32>().unwrap();

    let dir = matches.value_of("directory");
    let dir = if dir.is_some(){
        Some(dir.unwrap().to_string())
    }
    else{
        None
    };

    
    let problems = get_problems(contest_id).await?;

    let mut futures = Vec::new();
    for problem in problems.into_iter() {
        futures.push(get_problem_data(contest_id, problem))
    }
    let _results = futures::future::join_all(futures).await;

    let mut futures = Vec::new();
    for result in _results.iter() {
        let problem = result.as_ref().unwrap();
        for (i, data) in problem.ins.as_ref().unwrap().into_iter().enumerate() {
            futures.push(
                write_file(
                    format!(
                        "{}-{}",
                        problem.id.clone(),
                        problem.name.clone()
                    ), 
                    format!(".in.{}",i), 
                    data, 
                    &dir
                )
            );
        }
        for (i, data) in problem.outs.as_ref().unwrap().into_iter().enumerate() {
            futures.push(
                write_file(
                    format!(
                        "{}-{}",
                        problem.id.clone(),
                        problem.name.clone()
                    ), 
                    format!(".out.{}",i), 
                    data, 
                    &dir
                )
            );
        }
    }
    futures::future::join_all(futures).await;

    let cfg = config::get()?;

    let current_lang = cfg["current-lang"].as_str();
    match current_lang {
        Some(lang) => {
            for result in _results.iter() {
                let problem = result.as_ref().unwrap();
                let template = cfg["templates"][lang].as_str();
                match template{
                    Some(temp) => {
                        let temp_str = fs::read_to_string(temp)?;
                        match lang{
                            "cpp" => {
                                write_file(
                                    format!(
                                        "{}-{}",
                                        problem.id.clone(),
                                        problem.name.clone()
                                    ), 
                                    ".cpp".to_string(), 
                                    &temp_str, 
                                    &dir
                                ).await?;
                            }
                            _ => {
                                panic!("Language not supported {}", lang);
                            }
                        }
                    }
                    _ => {
                        panic!("No matching template found for lang {0}, use `config set template-{0} $TEMP`", lang);
                    }
                }
            }
        },
        _ => {
            panic!("No current lang found, use `config set lang $LANG`");
        }
    }

    Ok(())
}

async fn config_set(matches: &ArgMatches<'_>) -> Result<()>{
    let key = matches.value_of("KEY").unwrap();
    let value = matches.value_of("VALUE").unwrap();

    let mut cfg = config::get()?;

    if key == "lang"{
        cfg["current-lang"] = value.into();
    }
    else if key == "template-cpp"{
        cfg["templates"]["cpp"] = value.into();
    }

    config::set(cfg)?;

    Ok(())
}

async fn config(matches: &ArgMatches<'_>) -> Result<()>{
    if let Some(matches) = matches.subcommand_matches("set") {
        config_set(matches).await?;
    }

    Ok(())
}

async fn _get_tests_ins(dest: &str) -> Result<HashMap<String,String>>{
    let mut tests_ins = HashMap::new();
    for entry in glob(&format!("{}.in*", dest).to_string()).expect(""){
        match entry{
            Ok(entry) => {
                let entry_str = entry.to_str().unwrap().to_string();
                let main = entry_str.replace(".in","");
                tests_ins.insert(main.to_string(), entry_str);
            }
            Err(e) => {}
        }
    }
    Ok(tests_ins)
}
async fn _get_tests_outs(dest: &str) -> Result<HashMap<String,String>>{
    let mut tests_outs = HashMap::new();
    for entry in glob(&format!("{}.out*", dest).to_string()).expect(""){
        match entry{
            Ok(entry) => {
                let entry_str = entry.to_str().unwrap().to_string();
                let main = entry_str.replace(".out","");
                tests_outs.insert(main.to_string(), entry_str);
            }
            Err(e) => {}
        }
    }
    Ok(tests_outs)
}

async fn _get_source_dest(source: &str) -> Result<(String, String)>{
    let source = std::path::Path::new(source);
    let source = fs::canonicalize(source)?;
    let source_name = source.file_name().unwrap().to_str().unwrap();
    let dest_name = &source_name[..source_name.find(".").unwrap()];
    let dest = source.parent().unwrap().join(dest_name);

    let source = source.to_str().unwrap();
    let dest = dest.to_str().unwrap();

    Ok((source.to_string(), dest.to_string()))
}

async fn _test(source: &str) -> Result<()>{
    let cfg = config::get()?;
    
    let (source, dest) = _get_source_dest(source).await?;
    let tests_ins = _get_tests_ins(&dest).await?;
    let tests_outs = _get_tests_outs(&dest).await?;

    let current_lang = cfg["current-lang"].as_str();
    match current_lang {
        Some(lang) => {
            match lang{
                "cpp" => {
                    let os = cfg["test"]["cpp"].as_mapping();
                    match os{
                        Some(os) => {
                            if os.contains_key(&std::env::consts::OS.into()){
                                let test = cfg["test"]["cpp"][std::env::consts::OS].as_str().unwrap();
                                for (main, path) in tests_ins.iter() {
                                    let testtmp = format!("{}.tmp", tests_outs[main].as_str());
                                    let cmd = test
                                        .replace("{dest}",&dest)
                                        .replace("{testin}",path)
                                        .replace("{testtmp}", testtmp.as_str())
                                        .replace("{testout}", tests_outs[main].as_str());
                                    let output = std::process::Command::new("sh")
                                        .arg("-c")
                                        .arg(cmd)
                                        .output()
                                        .expect("Failed Testing");
                                        println!("{}",std::str::from_utf8(&output.stdout)?);
                                }
                            }
                            else{
                                panic!("Test: OS not supported {}",std::env::consts::OS)
                            }
                        }
                        _ => {}
                    }
                },
                _ => {
                    panic!("Language not supported {}", lang);
                }
            }
        },
        _ => {
            panic!("No current lang found, use `config set lang $LANG`");
        }
    }

    Ok(())
}

async fn _compile(source: &str) -> Result<()>{
    let cfg = config::get()?;
    
    let (source, dest) = _get_source_dest(source).await?;
    let tests_ins = _get_tests_ins(&dest).await?;
    let tests_outs = _get_tests_outs(&dest).await?;

    let current_lang = cfg["current-lang"].as_str();
    match current_lang {
        Some(lang) => {
            match lang{
                "cpp" => {
                    let os = cfg["compile"]["cpp"].as_mapping();
                    match os{
                        Some(os) => {
                            if os.contains_key(&std::env::consts::OS.into()){
                                let compile = cfg["compile"]["cpp"][std::env::consts::OS].as_str().unwrap();
                                let cmd = compile.replace("{src}",&source).replace("{dest}",&dest);
                                let output = std::process::Command::new("sh")
                                    .arg("-c")
                                    .arg(cmd)
                                    .output()
                                    .expect("Failed Compile");
                                println!("{}", std::str::from_utf8(&output.stdout)?);
                            }
                            else{
                                panic!("Compile: OS not supported {}",std::env::consts::OS)
                            }
                        }
                        _ => {}
                    }
                },
                _ => {
                    panic!("Language not supported {}", lang);
                }
            }
        },
        _ => {
            panic!("No current lang found, use `config set lang $LANG`");
        }
    }
    Ok(())
}

async fn test(matches: &ArgMatches<'_>) -> Result<()>{
    let source = matches.value_of("SOURCE").unwrap();
    _compile(source).await?;
    _test(source).await?;

    Ok(())
}

pub async fn cli() -> Result<()>{
    let yaml = load_yaml!("cli.yaml");
    let matches = App::from_yaml(yaml).get_matches();

    if let Some(matches) = matches.subcommand_matches("get") {
        get(matches).await?;
    }
    if let Some(matches) = matches.subcommand_matches("config") {
        config(matches).await?;
    }
    if let Some(matches) = matches.subcommand_matches("test") {
        test(matches).await?;
    }

    Ok(())
}