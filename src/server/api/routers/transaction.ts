import { z } from "zod";

import { createTRPCRouter, publicProcedure } from "~/server/api/trpc";

export const transactionRouter = createTRPCRouter({
    create: publicProcedure
        .input(z.object({ description: z.string().min(1), amount: z.number(), accountId: z.number() }))
        .mutation(async ({ ctx, input }) => {
        // simulate a slow db call
        await new Promise((resolve) => setTimeout(resolve, 1000));

        return ctx.db.transaction.create({
            data: {
                description: input.description,
                amount: input.amount,
                accountId: input.accountId
            },
        });
    }),

    getLatest: publicProcedure.query(({ ctx }) => {
        return ctx.db.transaction.findFirst({
            orderBy: {
                createdAt: "desc",
            },
        });
    }),

    getAll: publicProcedure.query(({ ctx }) => {
        return ctx.db.transaction.findMany();
    }),

    getById: publicProcedure
        .input(z.object({ id: z.number().optional() }))
        .query(({ ctx, input }) => {
        return ctx.db.transaction.findUnique({
            where: {
                id: input.id,
            },
        });
    }),

    update: publicProcedure
        .input(z.object({ id: z.number(), description: z.string().min(1), amount: z.number(), accountId: z.number() }))
        .mutation(({ ctx, input }) => {
        return ctx.db.transaction.update({
            where: {
                id: input.id,
            },
            data: {
                description: input.description,
                amount: input.amount,
                accountId: input.accountId
            },
        });
    }),

    delete: publicProcedure
        .input(z.object({ id: z.number() }))
        .mutation(({ ctx, input }) => {
        return ctx.db.transaction.delete({
            where: {
                id: input.id,
            },
        });
    }),

    getByAccountId: publicProcedure
        .input(z.object({ accountId: z.number() }))
        .query(({ ctx, input }) => {
        return ctx.db.transaction.findMany({
            where: {
                accountId: input.accountId
            }
        });
    })
});
