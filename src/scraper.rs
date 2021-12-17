use crate::Result;
use scraper::{Html,Selector};

pub struct CFProblem{
    pub id: String,
    pub name: String,
    pub ins: Option<Vec<String>>,
    pub outs: Option<Vec<String>>
}

impl std::fmt::Display for CFProblem{
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "<CFProblem id=\"{}\" name=\"{}\">", self.id, self.name)
    }
}

pub async fn get_problems(contest_id: u32) -> Result<Vec<CFProblem>> {
    println!("Retrieving problem info for contest: {}", contest_id);
    let resp = reqwest::get(
        format!(
            "https://codeforces.com/contest/{}", 
            contest_id
        )
    )
    .await?
    .text()
    .await?;
    
    let document = Html::parse_document(&resp);
    let prob_selc = Selector::parse("table.problems tbody tr").unwrap();
    let id_selc = Selector::parse("td.id a").unwrap();
    let name_selc = Selector::parse("td:nth-of-type(2n) a").unwrap();

    let mut problems = Vec::new();

    for elem in document.select(&prob_selc){
        let id = elem.select(&id_selc).next();
        let name = elem.select(&name_selc).next();

        if id.is_some() && name.is_some(){
            let id = id.unwrap().inner_html();
            let name = name.unwrap().inner_html();

            let id = id.trim().to_string();
            let name = name.replace("<!--","").replace("-->","").trim().to_string();
            
            let problem = CFProblem{id:id, name:name, ins:None, outs:None};
            problems.push(problem);
        }
    }
    println!("Retreived problem info for contest: {}", contest_id);
    println!(
        "Problems overview for conteset {}: {}",
        contest_id, 
        problems.iter().map(|p| p.id.clone()).collect::<Vec<_>>().join(", ")
    );

    Ok(problems)
}

pub async fn get_problem_data(contest_id: u32, mut problem: CFProblem) -> Result<CFProblem>{
    println!("Retrieving problem data for contest {} problem {}", contest_id, problem.id);
    let resp = reqwest::get(
        format!(
            "https://codeforces.com/contest/{}/problem/{}", 
            contest_id,
            problem.id
        )
    )
    .await?
    .text()
    .await?;

    let document = Html::parse_document(&resp);

    let input_selc = Selector::parse(".input pre").unwrap();
    let output_selc = Selector::parse(".output pre").unwrap();

    problem.ins = Some(Vec::new());
    for elem in document.select(&input_selc){
        problem.ins.as_mut().unwrap().push(elem.inner_html());
    }

    problem.outs = Some(Vec::new());
    for elem in document.select(&output_selc){
        problem.outs.as_mut().unwrap().push(elem.inner_html());
    }
    println!("Retrieved problem data for contest {} problem {}", contest_id, problem.id);

    Ok(problem)
}