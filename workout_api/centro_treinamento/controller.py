from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, status
from pydantic import UUID4
from sqlalchemy import select
from fastapi_pagination import LimitOffsetPage, add_pagination, paginate

from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.centro_treinamento.schemas import CentroTreinamentoIn, CentroTreinamentoOut
from workout_api.contrib.dependencies import DatabaseDependency

router = APIRouter()

@router.post(
    '/', 
    summary='Criar novo Centro de Treinameto', 
    status_code=status.HTTP_201_CREATED,
    response_model=CentroTreinamentoOut
)
async def post(
    db_session: DatabaseDependency, 
    centro_treinamento_in: CentroTreinamentoIn = Body(...)
) -> CentroTreinamentoOut:
    
    validacao_centro = (await db_session.execute(select(CentroTreinamentoModel).filter_by(nome=centro_treinamento_in.nome))).scalars().first()

    if validacao_centro and centro_treinamento_in.nome == validacao_centro.nome:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, detail=f'Já existe um centro de treinamento cadastrado com o nome: {validacao_centro.nome}')
    

    centro_treinamento_out = CentroTreinamentoOut(id=uuid4(), **centro_treinamento_in.model_dump())
    centro_treinamento_model = CentroTreinamentoModel(**centro_treinamento_out.model_dump())

    db_session.add(centro_treinamento_model)
    await db_session.commit()

    return centro_treinamento_out

@router.get(
    '/', 
    summary='Consultar todos os centros de treinamento', 
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[CentroTreinamentoOut]
)
async def query(
    db_session: DatabaseDependency,
) -> list[CentroTreinamentoOut]:
    centros_treinamento: list[CentroTreinamentoOut] = (await db_session.execute(select(CentroTreinamentoModel))).scalars().all()
    return paginate(centros_treinamento)

@router.get(
    '/{id}', 
    summary='Consultar um centro de treinamento pelo id', 
    status_code=status.HTTP_200_OK,
    response_model=CentroTreinamentoOut
)
async def query(
    id: UUID4,
    db_session: DatabaseDependency
) -> CentroTreinamentoOut:
    centro_treinamento: CentroTreinamentoOut = (await db_session.execute(select(CentroTreinamentoModel).filter_by(id=id))).scalars().first()

    if not centro_treinamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Centro de treinamento não encontrado no id: {id}')

    return centro_treinamento

add_pagination(router)