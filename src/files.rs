use crate::Result;
use std::path::Path;
use tokio::fs::File;
use tokio::io::AsyncWriteExt;

fn fileify(file: &str) -> Result<String>{
    Ok(file.to_lowercase().replace(" ","_").replace("-","_"))
}

pub async fn write_file(name: String, ext: String, data: &String, dir: &Option<String>) -> Result<()>{
    let dir = match dir{
        Some(dir) => dir.clone(), 
        _ => ".".to_string()
    };
    let dir = Path::new(&dir);
    let filename = fileify(format!("{}{}", name, ext).as_str())?;
    let path = dir.join(filename.clone());

    println!("Writing file: {}", filename);
    let mut file = File::create(path).await?;
    file.write_all(&data.as_bytes()).await?;
    println!("Done writing file: {}", filename);

    Ok(())
}