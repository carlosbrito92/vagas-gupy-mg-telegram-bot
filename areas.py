# -*- coding: utf-8 -*-
"""
Dicionário de áreas e palavras-chave usado para classificar vagas.

Como funciona a classificação (ver app.py -> classificar_vaga):
- O TÍTULO da vaga é obrigatório bater com pelo menos uma keyword da área.
- A DESCRIÇÃO é usada só como reforço opcional (não decide sozinha).
- A busca é "substring" case-insensitive (sem acentuação já normalizada).

Para adicionar uma área nova: crie uma chave nova no dicionário ÁREAS
com uma lista de keywords em minúsculo e sem acento.

Para adicionar uma keyword a uma área existente: só inclua o termo na
lista já existente.

O nome da área (chave do dicionário) é o que o usuário digita no comando
/definir — deve ser digitado exatamente igual (case-insensitive), então
evite acentos ou caracteres especiais nas chaves para facilitar o uso.
"""

AREAS = {

    "dados e ia": [
        "analista de dados", "data analyst",
        "cientista de dados", "data scientist",
        "engenheiro de dados", "data engineer",
        "engenheiro de analytics", "analytics engineer",
        "arquiteto de dados", "data architect",
        "engenheiro de machine learning", "machine learning engineer", "ml engineer",
        "engenheiro de ia", "engenheiro de inteligencia artificial",
        "business intelligence", " bi ", "analista de bi",
        "governanca de dados", "data governance",
        "prompt engineer", "especialista em ia generativa", "ia generativa",
        "inteligencia artificial",
    ],

    "desenvolvimento": [
        "desenvolvedor", "desenvolvedora", "developer", "programador", "programadora",
        "back-end", "backend", "back end",
        "front-end", "frontend", "front end",
        "full stack", "fullstack",
        "desenvolvedor mobile", "mobile developer", " ios ", "android", "flutter", "react native",
        "arquiteto de software", "software architect",
        "qa ", "quality assurance", "analista de testes", "engenheiro de testes", "teste de software",
        "game dev", "desenvolvedor de jogos",
        "sistemas embarcados", "embedded",
    ],

    "infra cloud e seguranca": [
        "devops",
        "sre ", "site reliability",
        "cloud engineer", "engenheiro de nuvem",
        "cloud architect", "arquiteto de nuvem",
        "sysadmin", "administrador de sistemas", "administrador de redes",
        "ciberseguranca", "cybersecurity", "seguranca da informacao",
        "appsec", "application security",
        "perito computacional", "forense digital", "analista forense",
        "inteligencia de ameacas", "threat intelligence", "osint",
    ],

    "produto e gestao tech": [
        "gerente de produto", "product manager",
        "product owner", " po ",
        "product designer", "ui/ux", "ux/ui", "ui designer", "ux designer",
        "tech lead", "lider tecnico",
        "engineering manager", "gerente de engenharia",
        "scrum master", "agile coach",
        "analista de requisitos", "analista de sistemas",
    ],

    "fiscal": [
        "fiscal", "tributario", "tributaria",
        "analista fiscal", "assistente fiscal", "coordenador fiscal",
        "contador", "contabil",
        "declaracoes acessorias", "sped",
    ],

    "financeiro": [
        "financeiro", "financeira",
        "analista financeiro", "assistente financeiro", "coordenador financeiro",
        "contas a pagar", "contas a receber",
        "tesouraria", "controladoria", "fp&a", "planejamento financeiro",
        "credito e cobranca", "analista de credito",
    ],

    "rh": [
        "recursos humanos", " rh ",
        "recrutamento e selecao", "recrutador", "recrutadora",
        "analista de rh", "generalista de rh",
        "departamento pessoal", " dp ",
        "people", "gente e gestao",
        "treinamento e desenvolvimento",
    ],

    "juridico": [
        "juridico", "advogado", "advogada",
        "analista juridico", "assistente juridico",
        "compliance", "paralegal",
        "contencioso", "societario",
    ],

    "marketing": [
        "marketing", "growth",
        "social media", "midias sociais",
        "trafego pago", "performance marketing",
        "analista de marketing", "coordenador de marketing",
        "conteudo", "copywriter", "redator", "redatora",
        "seo ", " sem ", "branding",
    ],

    "comercial e vendas": [
        "vendas", "vendedor", "vendedora",
        "comercial", "consultor de vendas", "consultora de vendas",
        "representante comercial", "executivo de contas", "account executive",
        "sdr ", "bdr ", "pre-vendas",
        "gerente comercial", "coordenador comercial",
        "key account",
    ],

    "logistica": [
        "logistica", "logistico",
        "supply chain", "cadeia de suprimentos",
        "analista de logistica", "coordenador de logistica",
        "estoque", "almoxarifado",
        "transporte e distribuicao", "expedicao",
        "compras", "suprimentos",
    ],

    "administrativo": [
        "administrativo", "administrativa",
        "auxiliar administrativo", "assistente administrativo", "analista administrativo",
        "secretaria", "recepcao",
        "back office", "rotinas administrativas",
    ],

}
